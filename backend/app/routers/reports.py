import csv
import io
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Category, Subscription, User
from app.schemas import SubscriptionOut
from app.services import exchange

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _monthly_cost(db, sub, base):
    amt = exchange.convert(db, sub.amount, sub.currency, base)
    n = max(1, sub.cycle_count)
    factor = {"day": 30 / n, "week": 52 / 12 / n, "month": 1 / n, "year": 1 / 12 / n}
    return amt * factor.get(sub.cycle, 1)


@router.get("/insights")
def insights(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """支出洞察：按分类的月度支出占比。"""
    base = user.base_currency
    subs = db.scalars(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.is_active.is_(True),
            Subscription.billing_type == "recurring",
        )
    ).all()
    cats = {c.id: c.name for c in db.scalars(select(Category)).all()}
    by_cat: dict[str, float] = {}
    for s in subs:
        name = cats.get(s.category_id, "未分类 / Uncategorized")
        by_cat[name] = by_cat.get(name, 0.0) + _monthly_cost(db, s, base)
    total = sum(by_cat.values())
    breakdown = sorted(
        (
            {"category": k, "monthly": round(v, 2), "percent": round(v / total * 100, 1) if total else 0}
            for k, v in by_cat.items()
        ),
        key=lambda x: x["monthly"],
        reverse=True,
    )
    return {"base_currency": base, "monthly_total": round(total, 2), "breakdown": breakdown}


@router.get("/export.csv")
def export_report_csv(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """导出报表 CSV：每个订阅的折算月度/年度成本（基准货币）+ 分类/状态。"""
    base = user.base_currency
    subs = db.scalars(select(Subscription).where(Subscription.user_id == user.id)).all()
    cats = {c.id: c.name for c in db.scalars(select(Category)).all()}
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["name", "category", "billing_type", "amount", "currency",
                f"monthly_{base}", f"yearly_{base}", "next_renewal_date", "active"])
    for s in subs:
        monthly = _monthly_cost(db, s, base) if s.billing_type == "recurring" else 0.0
        w.writerow([
            s.name, cats.get(s.category_id, ""), s.billing_type, s.amount, s.currency,
            round(monthly, 2), round(monthly * 12, 2),
            s.next_renewal_date.isoformat() if s.next_renewal_date else "",
            "1" if s.is_active else "0",
        ])
    return PlainTextResponse("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": "attachment; filename=easysub-report.csv"})


@router.get("/ranking", response_model=list[SubscriptionOut])
def ranking(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """支出排行：按月度成本从高到低。"""
    base = user.base_currency
    subs = db.scalars(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.is_active.is_(True),
            Subscription.billing_type == "recurring",
        )
    ).all()
    ranked = sorted(subs, key=lambda s: _monthly_cost(db, s, base), reverse=True)
    out = []
    for s in ranked:
        o = SubscriptionOut.model_validate(s)
        o.amount_in_base = round(_monthly_cost(db, s, base), 2)  # 此处复用为「月成本」
        out.append(o)
    return out


@router.get("/one-time", response_model=list[SubscriptionOut])
def one_time(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """永久购买 / 一次性买断清单。"""
    base = user.base_currency
    subs = db.scalars(
        select(Subscription).where(
            Subscription.user_id == user.id, Subscription.billing_type == "one_time"
        )
    ).all()
    out = []
    for s in subs:
        o = SubscriptionOut.model_validate(s)
        o.amount_in_base = round(exchange.convert(db, s.amount, s.currency, base), 2)
        out.append(o)
    return out


@router.get("/upcoming", response_model=list[SubscriptionOut])
def upcoming(
    days: int = 30, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """即将续费（未来 N 天）。"""
    base = user.base_currency
    today = date.today()
    horizon = today + timedelta(days=days)
    subs = db.scalars(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.is_active.is_(True),
            Subscription.billing_type == "recurring",
            Subscription.next_renewal_date.is_not(None),
        )
    ).all()
    items = sorted(
        [s for s in subs if today <= s.next_renewal_date <= horizon],
        key=lambda s: s.next_renewal_date,
    )
    out = []
    for s in items:
        o = SubscriptionOut.model_validate(s)
        o.amount_in_base = round(exchange.convert(db, s.amount, s.currency, base), 2)
        out.append(o)
    return out


@router.get("/expired", response_model=list[SubscriptionOut])
def expired(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """已过期：周期订阅且下次续费日已早于今天。"""
    base = user.base_currency
    today = date.today()
    subs = db.scalars(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.billing_type == "recurring",
            Subscription.next_renewal_date.is_not(None),
        )
    ).all()
    items = sorted(
        [s for s in subs if s.next_renewal_date < today],
        key=lambda s: s.next_renewal_date,
        reverse=True,
    )
    out = []
    for s in items:
        o = SubscriptionOut.model_validate(s)
        o.amount_in_base = round(exchange.convert(db, s.amount, s.currency, base), 2)
        out.append(o)
    return out


@router.get("/recent-payments")
def recent_payments(
    limit: int = 20, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """近期付款：最近一次续费（last_renewed_at）与一次性买断（start_date）合并按日期倒序。"""
    base = user.base_currency
    subs = db.scalars(
        select(Subscription).where(Subscription.user_id == user.id)
    ).all()
    cats = {c.id: c.name for c in db.scalars(select(Category)).all()}
    rows = []
    for s in subs:
        paid_on = s.last_renewed_at or (s.start_date if s.billing_type == "one_time" else None)
        if not paid_on:
            continue
        rows.append(
            {
                "id": s.id,
                "name": s.name,
                "plan": s.plan,
                "remark": s.remark,
                "icon": s.icon,
                "category": cats.get(s.category_id),
                "date": paid_on,
                "amount": round(s.amount, 2),
                "currency": s.currency,
                "amount_in_base": round(exchange.convert(db, s.amount, s.currency, base), 2),
                "billing_type": s.billing_type,
            }
        )
    rows.sort(key=lambda r: r["date"], reverse=True)
    return {"base_currency": base, "items": rows[:limit]}


@router.get("/category-detail")
def category_detail(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """分类明细：循环订阅（月成本）与永久购买（总额）按分类汇总。"""
    base = user.base_currency
    subs = db.scalars(
        select(Subscription).where(
            Subscription.user_id == user.id, Subscription.is_active.is_(True)
        )
    ).all()
    cats = {c.id: c.name for c in db.scalars(select(Category)).all()}

    def cat_name(s):
        return cats.get(s.category_id, "未分类 / Uncategorized")

    recurring_map: dict[str, dict] = {}
    onetime_map: dict[str, dict] = {}
    for s in subs:
        name = cat_name(s)
        if s.billing_type == "recurring":
            d = recurring_map.setdefault(name, {"category": name, "count": 0, "monthly": 0.0})
            d["count"] += 1
            d["monthly"] += _monthly_cost(db, s, base)
        else:
            amt = exchange.convert(db, s.amount, s.currency, base)
            d = onetime_map.setdefault(name, {"category": name, "count": 0, "total": 0.0})
            d["count"] += 1
            d["total"] += amt

    recurring = sorted(
        ({**v, "monthly": round(v["monthly"], 2)} for v in recurring_map.values()),
        key=lambda x: x["monthly"],
        reverse=True,
    )
    one_time = sorted(
        ({**v, "total": round(v["total"], 2)} for v in onetime_map.values()),
        key=lambda x: x["total"],
        reverse=True,
    )
    return {
        "base_currency": base,
        "recurring": recurring,
        "one_time": one_time,
        "recurring_monthly_total": round(sum(r["monthly"] for r in recurring), 2),
        "one_time_total": round(sum(o["total"] for o in one_time), 2),
    }
