from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import activity
from app.database import get_db
from app.deps import get_current_user
from app.models import NotificationLog, User
from app.schemas import TelegramTestIn
from app.services import notify, scheduler, telegram

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# ---- 多渠道通知配置 -------------------------------------------------------- #
class NotifyConfigIn(BaseModel):
    config: dict


class NotifyTestIn(BaseModel):
    channel: str
    config: dict | None = None  # 可传入未保存的配置用于即时测试


@router.get("/config")
def get_notify_config(user: User = Depends(get_current_user)):
    """读取当前用户的全部通知渠道配置（含默认值与旧版 Telegram 回退）。"""
    return {"config": notify.load_config(user)}


@router.put("/config")
def save_notify_config(
    payload: NotifyConfigIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存通知渠道配置。"""
    cfg = notify.apply_config(user, payload.config)
    db.commit()
    enabled = [c for c in notify.CHANNELS if cfg.get(c, {}).get("enabled")]
    activity.log("notify.config", f"更新通知配置（启用：{', '.join(enabled) or '无'}）", user=user)
    return {"ok": True, "config": cfg}


@router.post("/test")
def test_notify(payload: NotifyTestIn, user: User = Depends(get_current_user)):
    """向指定渠道发送一条测试消息。config 省略时用已保存配置。"""
    if payload.channel not in notify.CHANNELS:
        raise HTTPException(400, f"未知渠道：{payload.channel}")
    conf = (payload.config or {}) or notify.load_config(user).get(payload.channel, {})
    subject = "省心订阅 EasySub · 测试通知"
    text = (
        "✅ *连接成功！*\n\n这是一条来自 *省心订阅 EasySub* 的测试通知。\n"
        "之后订阅快到期时，我会通过该渠道带上完整信息提前提醒你 🎉"
    )
    try:
        notify.send_one(payload.channel, conf, subject, text)
    except Exception as e:  # noqa: BLE001
        activity.log("notify.test", f"{payload.channel} 测试发送失败：{e}", user=user, level="error")
        raise HTTPException(502, f"发送失败：{e}")
    activity.log("notify.test", f"发送了 {payload.channel} 测试通知", user=user)
    return {"ok": True}


def _tg_args(user: User, override_token: str | None = None) -> dict:
    return {
        "token": override_token or user.telegram_bot_token,
        "api_base": user.telegram_api_base,
        "proxy": user.telegram_proxy,
    }


@router.get("/telegram/me")
def telegram_me(user: User = Depends(get_current_user)):
    """验证 Bot Token 是否有效（getMe）。"""
    if not user.telegram_bot_token:
        raise HTTPException(400, "请先填写 Bot Token")
    try:
        return telegram.get_me(**_tg_args(user))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Telegram getMe 失败：{e}")


@router.get("/telegram/updates")
def telegram_updates(user: User = Depends(get_current_user)):
    """辅助绑定：用户向 Bot 发消息后，从这里读取 chat_id。"""
    if not user.telegram_bot_token:
        raise HTTPException(400, "请先填写 Bot Token")
    try:
        return telegram.get_updates(**_tg_args(user))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Telegram getUpdates 失败：{e}")


@router.post("/telegram/test")
def telegram_test(
    payload: TelegramTestIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """向当前用户（或指定 chat_id）发送一条测试消息。"""
    token = payload.bot_token or user.telegram_bot_token
    if not token:
        raise HTTPException(400, "请先填写 Bot Token")
    chat_id = payload.chat_id or user.telegram_chat_id
    if not chat_id:
        raise HTTPException(400, "未填写 Chat ID")
    try:
        telegram.send_message(
            chat_id,
            "✅ *连接成功！*\n\n"
            "省心订阅 *EasySub* 已和你的 Telegram 绑定～\n"
            "之后有订阅快到期，我会带上完整信息提前提醒你，"
            "保号 / 续费再也不怕忘记啦 🎉",
            token=token,
            api_base=user.telegram_api_base,
            proxy=user.telegram_proxy,
        )
    except Exception as e:  # noqa: BLE001
        activity.log("telegram.test", f"测试消息发送失败：{e}", user=user, level="error")
        raise HTTPException(502, f"发送失败：{e}")
    activity.log("telegram.test", "发送了 Telegram 测试消息", user=user)
    return {"ok": True}


@router.post("/run-scan")
def run_scan(user: User = Depends(get_current_user)):
    """手动触发一次到期扫描（用于测试）。"""
    return scheduler.run_reminder_scan()


@router.get("/logs")
def logs(limit: int = 50, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(NotificationLog)
        .where(NotificationLog.user_id == user.id)
        .order_by(NotificationLog.sent_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": r.id,
            "subscription_id": r.subscription_id,
            "days_before": r.days_before,
            "status": r.status,
            "message": r.message,
            "sent_at": r.sent_at,
        }
        for r in rows
    ]
