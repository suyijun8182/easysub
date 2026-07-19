"""对外集成：供 Home Assistant / 自动化脚本用 API Token 轮询的摘要端点。

用法：创建 API Token 后，用 `Authorization: Bearer <token>` 访问
GET /api/integrations/summary，即可拿到即将续费与统计，供 HA 传感器展示/告警。
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Subscription, User
from app.services import exchange

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _monthly(db, sub, base):
    amt = exchange.convert(db, sub.amount, sub.currency, base)
    n = max(1, sub.cycle_count)
    factor = {"day": 30 / n, "week": 52 / 12 / n, "month": 1 / n, "year": 1 / 12 / n}
    return amt * factor.get(sub.cycle, 1)


@router.get("/summary")
def summary(days: int = 30, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """订阅摘要：即将续费列表 + 计数 + 月度支出。适合 HA 传感器轮询。"""
    base = user.base_currency
    today = date.today()
    horizon = today + timedelta(days=max(1, min(365, days)))
    subs = db.scalars(select(Subscription).where(
        Subscription.user_id == user.id, Subscription.is_active.is_(True)
    )).all()
    recurring = [s for s in subs if s.billing_type == "recurring"]
    monthly = sum(_monthly(db, s, base) for s in recurring)
    upcoming = sorted(
        [s for s in recurring if s.next_renewal_date and today <= s.next_renewal_date <= horizon],
        key=lambda s: s.next_renewal_date,
    )
    overdue = [s for s in recurring if s.next_renewal_date and s.next_renewal_date < today]
    return {
        "base_currency": base,
        "active_count": len(subs),
        "monthly_spend": round(monthly, 2),
        "yearly_spend": round(monthly * 12, 2),
        "overdue_count": len(overdue),
        "upcoming_count": len(upcoming),
        "upcoming": [
            {
                "name": s.name,
                "date": s.next_renewal_date.isoformat(),
                "days_left": (s.next_renewal_date - today).days,
                "amount": s.amount,
                "currency": s.currency,
            }
            for s in upcoming[:50]
        ],
    }
