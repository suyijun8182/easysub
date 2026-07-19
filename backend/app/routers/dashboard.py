from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing import add_cycle
from app.database import get_db
from app.deps import get_current_user
from app.models import Subscription, User
from app.schemas import DashboardOut, SubscriptionOut
from app.services import exchange

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _monthly_cost_in_base(db: Session, sub: Subscription, base: str) -> float:
    """把一个周期订阅折算为「每月」成本（基准货币）。"""
    amt = exchange.convert(db, sub.amount, sub.currency, base)
    n = max(1, sub.cycle_count)
    if sub.cycle == "day":
        return amt / n * 30
    if sub.cycle == "week":
        return amt / n * 52 / 12
    if sub.cycle == "month":
        return amt / n
    if sub.cycle == "year":
        return amt / n / 12
    return amt


@router.get("", response_model=DashboardOut)
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    base = user.base_currency
    today = date.today()
    subs = db.scalars(
        select(Subscription).where(
            Subscription.user_id == user.id, Subscription.is_active.is_(True)
        )
    ).all()

    recurring = [s for s in subs if s.billing_type == "recurring"]
    month_spend = sum(_monthly_cost_in_base(db, s, base) for s in recurring)
    year_spend = month_spend * 12

    # 即将到期（未来 30 天内）
    horizon = today + timedelta(days=30)
    upcoming = sorted(
        [
            s
            for s in recurring
            if s.next_renewal_date and today <= s.next_renewal_date <= horizon
        ],
        key=lambda s: s.next_renewal_date,
    )[:8]

    recent = sorted(subs, key=lambda s: s.created_at, reverse=True)[:8]

    def conv(items):
        out = []
        for s in items:
            o = SubscriptionOut.model_validate(s)
            o.amount_in_base = round(exchange.convert(db, s.amount, s.currency, base), 2)
            out.append(o)
        return out

    return DashboardOut(
        base_currency=base,
        month_spend=round(month_spend, 2),
        year_spend=round(year_spend, 2),
        active_count=len(subs),
        monthly_budget=user.monthly_budget,
        upcoming=conv(upcoming),
        recent=conv(recent),
    )
