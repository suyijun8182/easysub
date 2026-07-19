import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import activity, icon_library
from app.billing import add_cycle, compute_next_renewal
from app.database import get_db
from app.deps import get_current_user
from app.models import Category, Subscription, User
from app.schemas import SubscriptionIn, SubscriptionOut, SubscriptionUpdate
from app.security import verify_password
from app.services import exchange

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


def _to_out(db: Session, sub: Subscription, base_currency: str) -> SubscriptionOut:
    out = SubscriptionOut.model_validate(sub)
    out.amount_in_base = round(
        exchange.convert(db, sub.amount, sub.currency, base_currency), 2
    )
    return out


@router.get("", response_model=list[SubscriptionOut])
def list_subs(
    active: bool | None = None,
    billing_type: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Subscription).where(Subscription.user_id == user.id)
    if active is not None:
        stmt = stmt.where(Subscription.is_active.is_(active))
    if billing_type:
        stmt = stmt.where(Subscription.billing_type == billing_type)
    stmt = stmt.order_by(
        Subscription.sort,
        Subscription.next_renewal_date.is_(None),
        Subscription.next_renewal_date,
    )
    rows = db.scalars(stmt).all()
    return [_to_out(db, s, user.base_currency) for s in rows]


@router.post("", response_model=SubscriptionOut)
def create_sub(
    payload: SubscriptionIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump()
    data["start_date"] = data.get("start_date") or date.today()
    # 附加信息：常用订阅名自动补全官方网站
    if not data.get("url"):
        site = icon_library.website_for_name(data.get("name", ""))
        if site:
            data["url"] = site
    if data["billing_type"] == "recurring" and not data.get("next_renewal_date"):
        data["next_renewal_date"] = compute_next_renewal(
            data["start_date"], data["cycle"], data["cycle_count"]
        )
    if data["billing_type"] == "one_time":
        data["next_renewal_date"] = None
        data["auto_renew"] = False
    sub = Subscription(**data, user_id=user.id)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    activity.log("subscription.create", f"新增订阅「{sub.name}」", user=user)
    return _to_out(db, sub, user.base_currency)


# ---------- CSV 批量导入 / 导出（须声明在 /{sub_id} 之前，避免路径被吞） ----------
_CSV_FIELDS = [
    "name", "plan", "category", "amount", "currency", "billing_type", "cycle",
    "cycle_count", "start_date", "next_renewal_date", "remark", "url", "remind_days_before",
]


@router.get("/export.csv")
def export_csv(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """导出当前用户的订阅为 CSV。"""
    subs = db.scalars(select(Subscription).where(Subscription.user_id == user.id)).all()
    cat_map = {c.id: c.name for c in db.scalars(
        select(Category).where(or_(Category.user_id == user.id, Category.is_system.is_(True)))
    ).all()}
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(_CSV_FIELDS)
    for s in subs:
        w.writerow([
            s.name, s.plan or "", cat_map.get(s.category_id, ""), s.amount, s.currency,
            s.billing_type, s.cycle, s.cycle_count,
            s.start_date.isoformat() if s.start_date else "",
            s.next_renewal_date.isoformat() if s.next_renewal_date else "",
            s.remark or "", s.url or "", s.remind_days_before,
        ])
    return PlainTextResponse("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": "attachment; filename=easysub-subscriptions.csv"})


class CsvImportIn(BaseModel):
    content: str


@router.post("/import-csv")
def import_csv(payload: CsvImportIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """从 CSV 文本批量导入订阅。分类按名称匹配（缺失则新建）。"""
    text = (payload.content or "").lstrip("﻿")
    reader = csv.DictReader(io.StringIO(text))
    existing_cats = {
        c.name: c for c in db.scalars(
            select(Category).where(or_(Category.user_id == user.id, Category.is_system.is_(True)))
        ).all()
    }

    def _num(v, default):
        try:
            return type(default)(v)
        except (TypeError, ValueError):
            return default

    def _d(v):
        try:
            return date.fromisoformat(v.strip()) if v and v.strip() else None
        except (TypeError, ValueError):
            return None

    count = 0
    for row in reader:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        cat_name = (row.get("category") or "").strip()
        cat_id = None
        if cat_name:
            cat = existing_cats.get(cat_name)
            if not cat:
                cat = Category(name=cat_name, user_id=user.id, is_system=False)
                db.add(cat)
                db.flush()
                existing_cats[cat_name] = cat
            cat_id = cat.id
        billing_type = (row.get("billing_type") or "recurring").strip() or "recurring"
        start = _d(row.get("start_date")) or date.today()
        sub = Subscription(
            user_id=user.id, name=name, plan=(row.get("plan") or None),
            category_id=cat_id, amount=_num(row.get("amount"), 0.0),
            currency=(row.get("currency") or user.base_currency).strip() or user.base_currency,
            billing_type=billing_type, cycle=(row.get("cycle") or "month").strip() or "month",
            cycle_count=_num(row.get("cycle_count"), 1) or 1, start_date=start,
            next_renewal_date=_d(row.get("next_renewal_date")),
            remark=(row.get("remark") or None), url=(row.get("url") or None),
            remind_days_before=(row.get("remind_days_before") or "7,6,5,4,3,2,1").strip() or "7,6,5,4,3,2,1",
        )
        if billing_type == "recurring" and not sub.next_renewal_date:
            sub.next_renewal_date = compute_next_renewal(start, sub.cycle, sub.cycle_count)
        if billing_type == "one_time":
            sub.next_renewal_date = None
            sub.auto_renew = False
        db.add(sub)
        count += 1
    db.commit()
    activity.log("subscription.import_csv", f"CSV 导入了 {count} 个订阅", user=user)
    return {"ok": True, "imported": count}


@router.get("/{sub_id}", response_model=SubscriptionOut)
def get_sub(sub_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = db.get(Subscription, sub_id)
    if not sub or sub.user_id != user.id:
        raise HTTPException(404, "订阅不存在")
    return _to_out(db, sub, user.base_currency)


@router.put("/{sub_id}", response_model=SubscriptionOut)
def update_sub(
    sub_id: int,
    payload: SubscriptionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = db.get(Subscription, sub_id)
    if not sub or sub.user_id != user.id:
        raise HTTPException(404, "订阅不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(sub, k, v)
    if sub.billing_type == "one_time":
        sub.next_renewal_date = None
    db.commit()
    db.refresh(sub)
    return _to_out(db, sub, user.base_currency)


class RenewIn(BaseModel):
    # today：保号类——从今天起 + 周期（并把开始日期重置为今天）
    # due  ：循环类——从原到期日起 + 周期（提前续费不浪费已付时间）
    mode: str = "today"
    # 兼容旧版字段
    reset_start_date: bool | None = None


@router.post("/{sub_id}/renew", response_model=SubscriptionOut)
def renew_sub(
    sub_id: int,
    payload: RenewIn | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记已续费。两种模式：
    - today：从【今天】起 + 一个周期，并把开始日期重置为今天（手机保号等场景）。
    - due  ：从【原到期日】起 + 一个周期（常规循环订阅，提前续费不丢已付时间）。
    """
    sub = db.get(Subscription, sub_id)
    if not sub or sub.user_id != user.id:
        raise HTTPException(404, "订阅不存在")
    if sub.billing_type != "recurring":
        raise HTTPException(400, "一次性买断项目无需续费")
    today = date.today()

    mode = (payload.mode if payload else "today") or "today"
    if payload and payload.reset_start_date is True:
        mode = "today"  # 兼容旧前端

    if mode == "due":
        base = sub.next_renewal_date or today
        sub.next_renewal_date = add_cycle(base, sub.cycle, sub.cycle_count)
    else:  # today
        sub.start_date = today
        sub.next_renewal_date = add_cycle(today, sub.cycle, sub.cycle_count)

    sub.last_renewed_at = today
    db.commit()
    db.refresh(sub)
    activity.log(
        "subscription.renew",
        f"续费「{sub.name}」（{mode}），下次到期 {sub.next_renewal_date}",
        user=user,
    )
    return _to_out(db, sub, user.base_currency)


class ReorderIn(BaseModel):
    # 同一分类内、按新顺序排列的订阅 id 列表
    ordered_ids: list[int]


@router.post("/reorder")
def reorder_subs(
    payload: ReorderIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存同一分类内订阅的拖拽顺序（按列表下标写入 sort）。"""
    for index, sid in enumerate(payload.ordered_ids):
        sub = db.get(Subscription, sid)
        if sub and sub.user_id == user.id:
            sub.sort = index
    db.commit()
    return {"ok": True}


class DeleteIn(BaseModel):
    password: str


@router.delete("/{sub_id}")
def delete_sub(
    sub_id: int,
    payload: DeleteIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除订阅前需校验当前用户密码，防止误删/他人操作。"""
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(403, "密码不正确")
    sub = db.get(Subscription, sub_id)
    if not sub or sub.user_id != user.id:
        raise HTTPException(404, "订阅不存在")
    name = sub.name
    db.delete(sub)
    db.commit()
    activity.log("subscription.delete", f"删除订阅「{name}」", user=user, level="warn")
    return {"ok": True}
