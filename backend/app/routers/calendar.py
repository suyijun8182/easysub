"""日历订阅（.ics feed）：把订阅的续费日导出为 iCalendar，可在 Apple/Google/Outlook
日历中「订阅网络日历」，续费日直接进日历并由系统原生提醒。

链接形如 /api/calendar/<token>/easysub.ics，token 为每用户私有随机串，可重置。
"""
import secrets
from datetime import date, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Subscription, User

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


def _ensure_token(db: Session, user: User) -> str:
    if not user.calendar_token:
        user.calendar_token = secrets.token_urlsafe(24)
        db.commit()
    return user.calendar_token


@router.get("/token")
def get_token(
    reset: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取（或重置）当前用户的日历订阅链接。返回相对路径，由前端拼接实际域名。"""
    if reset or not user.calendar_token:
        user.calendar_token = secrets.token_urlsafe(24)
        db.commit()
    return {
        "token": user.calendar_token,
        "path": f"/api/calendar/{user.calendar_token}/easysub.ics",
    }


def _esc(text: str) -> str:
    if not text:
        return ""
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def _fold(line: str) -> str:
    """iCalendar 每行不超过 75 字节，超出需折行（简单按字符折）。"""
    if len(line) <= 73:
        return line
    out, s = [], line
    while len(s) > 73:
        out.append(s[:73])
        s = " " + s[73:]
    out.append(s)
    return "\r\n".join(out)


@router.get("/{token}/easysub.ics")
def ics_feed(token: str, db: Session = Depends(get_db)):
    """返回该 token 对应用户的订阅续费日历（无需登录，凭 token 访问）。"""
    user = db.scalar(select(User).where(User.calendar_token == token))
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//EasySub//Subscription Renewals//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:EasySub 续费提醒",
    ]
    if user:
        subs = db.scalars(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.is_active.is_(True),
                Subscription.show_in_calendar.is_(True),
                Subscription.next_renewal_date.is_not(None),
            )
        ).all()
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        for s in subs:
            d: date = s.next_renewal_date
            dt = d.strftime("%Y%m%d")
            summary = f"续费：{s.name}"
            if s.amount:
                summary += f"（{s.amount:.2f} {s.currency}）"
            desc_parts = [f"套餐：{s.plan}" if s.plan else "", f"备注：{s.remark}" if s.remark else ""]
            desc = " ".join(p for p in desc_parts if p)
            lines += [
                "BEGIN:VEVENT",
                f"UID:easysub-{s.id}-{dt}@easysub",
                f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{dt}",
                _fold(f"SUMMARY:{_esc(summary)}"),
                _fold(f"DESCRIPTION:{_esc(desc)}") if desc else "DESCRIPTION:",
                # 提前 1 天弹提醒
                "BEGIN:VALARM",
                "TRIGGER:-P1D",
                "ACTION:DISPLAY",
                _fold(f"DESCRIPTION:{_esc(summary)}"),
                "END:VALARM",
                "END:VEVENT",
            ]
    lines.append("END:VCALENDAR")
    body = "\r\n".join(lines) + "\r\n"
    return PlainTextResponse(body, media_type="text/calendar; charset=utf-8")
