from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import database
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Subscription, User

router = APIRouter(prefix="/api/system", tags=["system"])

APP_VERSION = "1.9.0"


@router.get("/info")
def info(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    your_total = db.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.user_id == user.id)
    )
    your_active = db.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.user_id == user.id, Subscription.is_active.is_(True))
    )
    data = {
        "version": APP_VERSION,
        "db_configured": database.is_configured(),
        "server_time": datetime.now().isoformat(timespec="seconds"),
        "timezone": settings.tz,
        "reminder_scan_time": settings.reminder_scan_time,
        "your_subscriptions": your_total,
        "your_active": your_active,
        "telegram_enabled": user.telegram_enabled,
    }
    if user.is_admin:
        data["total_users"] = db.scalar(select(func.count()).select_from(User))
        data["total_subscriptions"] = db.scalar(select(func.count()).select_from(Subscription))
    return data
