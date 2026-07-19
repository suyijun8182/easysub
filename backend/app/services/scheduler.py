"""定时任务：每日扫描即将到期的订阅并通过 Telegram 提醒。"""
from datetime import date, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app import activity, database
from app.config import settings
from app.models import Category, NotificationLog, PaymentMethod, Subscription, User
from app.services import exchange, notify

_scheduler: BackgroundScheduler | None = None


def _parse_days(raw: str) -> list[int]:
    out = []
    for part in (raw or "").split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out


def _already_sent(db, sub_id: int, days_before: int, on_day: date) -> bool:
    rows = db.scalars(
        select(NotificationLog).where(
            NotificationLog.subscription_id == sub_id,
            NotificationLog.days_before == days_before,
            NotificationLog.status == "sent",
        )
    ).all()
    return any(r.sent_at and r.sent_at.date() == on_day for r in rows)


def run_reminder_scan() -> dict:
    """核心扫描逻辑（可被定时器或手动触发调用）。"""
    today = date.today()
    sent, failed = 0, 0
    if database.SessionLocal is None:
        return {"sent": 0, "failed": 0, "skipped": "数据库未配置"}
    db = database.SessionLocal()
    try:
        subs = db.scalars(
            select(Subscription).where(
                Subscription.is_active.is_(True),
                Subscription.billing_type == "recurring",
                Subscription.next_renewal_date.is_not(None),
            )
        ).all()
        for sub in subs:
            user = db.get(User, sub.user_id)
            if not user:
                continue
            # 只要启用了任意一个通知渠道即发送
            cfg = notify.load_config(user)
            if not any(cfg.get(c, {}).get("enabled") for c in notify.CHANNELS):
                continue
            days_left = (sub.next_renewal_date - today).days
            for n in _parse_days(sub.remind_days_before):
                if days_left == n and not _already_sent(db, sub.id, n, today):
                    text_md = _build_text(db, sub, user, days_left)
                    subject = f"续费提醒：{sub.name}"
                    results = notify.dispatch(
                        user, subject, notify._strip_md(text_md), text_md=text_md
                    )
                    ok_ch = [r["channel"] for r in results if r.get("ok")]
                    err = [f"{r['channel']}: {r['error']}" for r in results if not r.get("ok")]
                    # channel 列仅 16 字符：单渠道存名字，多渠道存紧凑摘要
                    if len(ok_ch) == 1:
                        ch_label = ok_ch[0]
                    elif ok_ch:
                        ch_label = f"multi:{len(ok_ch)}"
                    else:
                        ch_label = "none"
                    log = NotificationLog(
                        subscription_id=sub.id,
                        user_id=user.id,
                        days_before=n,
                        channel=ch_label,
                        status="sent" if ok_ch else "failed",
                        message=text_md if ok_ch else "; ".join(err) or "无可用渠道",
                        sent_at=datetime.utcnow(),
                    )
                    db.add(log)
                    if ok_ch:
                        sent += 1
                        activity.log(
                            "notify.reminder",
                            f"已提醒「{sub.name}」（提前 {n} 天，渠道：{', '.join(ok_ch)}）",
                            user=user,
                        )
                    if err:
                        failed += 1
                        activity.log(
                            "notify.reminder",
                            f"提醒「{sub.name}」部分渠道失败：{'; '.join(err)}",
                            user=user,
                            level="error" if not ok_ch else "warn",
                        )
        db.commit()
    finally:
        db.close()
    return {"sent": sent, "failed": failed}


_CYCLE_CN = {"day": "天", "week": "周", "month": "个月", "year": "年"}


def _escape_md(text: str) -> str:
    """转义 Markdown 中可能破坏排版的下划线/星号，保证名称等原样显示。"""
    if not text:
        return ""
    for ch in ("_", "*", "`", "["):
        text = text.replace(ch, "\\" + ch)
    return text


def _build_text(db, sub: Subscription, user: User, days_left: int) -> str:
    """构造一条信息完整、措辞友好的续费提醒。"""
    amount = f"{sub.amount:.2f} {sub.currency}"
    in_base = exchange.convert(db, sub.amount, sub.currency, user.base_currency)
    base_str = ""
    if abs(in_base - sub.amount) > 1e-6 or sub.currency != user.base_currency:
        base_str = f"（≈ {in_base:.2f} {user.base_currency}）"

    if days_left <= 0:
        when = "⚠️ *今天到期*"
        head = "🔔 *续费提醒*｜今天就到期啦"
    else:
        when = f"还有 *{days_left}* 天"
        head = f"🔔 *续费提醒*｜还有 {days_left} 天到期"

    # 关联信息
    cat = db.get(Category, sub.category_id) if sub.category_id else None
    pm = db.get(PaymentMethod, sub.payment_method_id) if sub.payment_method_id else None
    unit = _CYCLE_CN.get(sub.cycle, sub.cycle)
    cycle_str = f"每 {sub.cycle_count} {unit}" if (sub.cycle_count or 1) > 1 else f"每{unit}"

    lines = [head, ""]
    title = _escape_md(sub.name)
    if sub.plan:
        title += f"（{_escape_md(sub.plan)}）"
    lines.append(f"📦 项目：*{title}*")
    if cat:
        lines.append(f"🗂️ 分类：{_escape_md(cat.name)}")
    lines.append(f"📅 到期：*{sub.next_renewal_date}*（{when}）")
    lines.append(f"💰 金额：*{amount}*{base_str} · {cycle_str}")
    if pm:
        lines.append(f"💳 付款：{_escape_md(pm.name)}")
    lines.append(f"🔁 自动续费：{'开' if sub.auto_renew else '关'}")
    if sub.family_members:
        lines.append(f"👨‍👩‍👧 家庭成员：{_escape_md('、'.join(sub.family_members))}")
    if sub.remark:
        lines.append(f"📝 备注：{_escape_md(sub.remark)}")
    if sub.url:
        lines.append(f"🔗 官网：{sub.url}")

    lines.append("")
    if days_left <= 0:
        lines.append("👉 别忘了今天处理一下，保号 / 续费就万无一失～")
    else:
        lines.append("👉 早点安排续费，省心又安心，避免到期失效～")
    return "\n".join(lines)


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    hour, minute = 9, 0
    try:
        hour, minute = (int(x) for x in settings.reminder_scan_time.split(":"))
    except Exception:  # noqa: BLE001
        pass

    _scheduler = BackgroundScheduler(timezone=settings.tz)
    _scheduler.add_job(
        run_reminder_scan,
        CronTrigger(hour=hour, minute=minute),
        id="daily_reminder_scan",
        replace_existing=True,
    )
    # 每天凌晨 4 点刷新汇率
    _scheduler.add_job(
        _refresh_rates_job,
        CronTrigger(hour=4, minute=0),
        id="daily_rate_refresh",
        replace_existing=True,
    )
    _scheduler.start()


def _refresh_rates_job() -> None:
    if database.SessionLocal is None:
        return
    db = database.SessionLocal()
    try:
        exchange.refresh_rates(db)
    except Exception:  # noqa: BLE001
        pass
    finally:
        db.close()


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
