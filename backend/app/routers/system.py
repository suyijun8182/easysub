import re
import time
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import database
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Subscription, User

router = APIRouter(prefix="/api/system", tags=["system"])

APP_VERSION = "1.10.0"
GITHUB_REPO = "suyijun8182/easysub"

# 版本检查结果缓存（避免频繁请求 GitHub，未认证限流 60 次/小时）
_ver_cache: dict = {"at": 0.0, "data": None}
_VER_TTL = 6 * 3600


def _parse_semver(v: str):
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", v.strip())
    return tuple(int(x) for x in m.groups()) if m else None


def _fetch_latest() -> dict:
    """从 GitHub tags 取最新版本号。失败则返回仅含当前版本的结果。"""
    result = {
        "current": APP_VERSION,
        "latest": None,
        "update_available": False,
        "release_url": f"https://github.com/{GITHUB_REPO}/releases",
        "error": None,
    }
    try:
        with httpx.Client(timeout=8, headers={"Accept": "application/vnd.github+json"}) as c:
            r = c.get(f"https://api.github.com/repos/{GITHUB_REPO}/tags", params={"per_page": 30})
            r.raise_for_status()
            versions = []
            for tag in r.json():
                sv = _parse_semver(tag.get("name", ""))
                if sv:
                    versions.append((sv, tag["name"]))
            if versions:
                versions.sort(reverse=True)
                latest_tuple, latest_name = versions[0]
                result["latest"] = latest_name.lstrip("v")
                cur = _parse_semver(APP_VERSION) or (0, 0, 0)
                result["update_available"] = latest_tuple > cur
                result["release_url"] = f"https://github.com/{GITHUB_REPO}/releases/tag/{latest_name}"
    except Exception as e:  # noqa: BLE001
        result["error"] = f"{type(e).__name__}"
    return result


@router.get("/version-check")
def version_check(refresh: bool = False, user: User = Depends(get_current_user)):
    """检查是否有新版本（对比 GitHub 最新 tag）。结果缓存 6 小时。"""
    now = time.monotonic()
    if refresh or not _ver_cache["data"] or (now - _ver_cache["at"]) > _VER_TTL:
        _ver_cache["data"] = _fetch_latest()
        _ver_cache["at"] = now
    return {**_ver_cache["data"], "checked_at": datetime.now().isoformat(timespec="seconds")}


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
