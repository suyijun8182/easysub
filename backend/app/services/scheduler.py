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
            # 免打扰时段：非紧急（>=2 天）提醒暂缓，紧急（今天/明天）仍照常发；
            # 暂缓的提醒不写已发记录，次日扫描会再次评估。
            if days_left >= 2 and notify.in_quiet_hours(user):
                continue
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


def run_date_reminders() -> dict:
    """试用期结束 / 取消截止 / 付款卡到期 提醒（每日检查）。

    用 NotificationLog.days_before 的哨兵值区分类型并去重：-1 试用、-2 取消、-3 卡到期。
    """
    if database.SessionLocal is None:
        return {"sent": 0, "skipped": "数据库未配置"}
    today = date.today()
    sent = 0
    db = database.SessionLocal()
    try:
        subs = db.scalars(select(Subscription).where(Subscription.is_active.is_(True))).all()
        for sub in subs:
            user = db.get(User, sub.user_id)
            if not user:
                continue
            cfg = notify.load_config(user)
            if not any(cfg.get(c, {}).get("enabled") for c in notify.CHANNELS):
                continue
            events = []  # (code, subject, text)
            if sub.trial_end:
                d = (sub.trial_end - today).days
                if d in (3, 1, 0):
                    when = "今天" if d == 0 else f"还有 {d} 天"
                    events.append((-1, f"试用将结束：{sub.name}",
                                   f"「{sub.name}」的免费试用{when}结束（{sub.trial_end}）。"
                                   f"如不想被自动扣费，请及时取消或确认转正。"))
            if sub.cancel_by:
                d = (sub.cancel_by - today).days
                if d in (3, 1, 0):
                    when = "今天" if d == 0 else f"还有 {d} 天"
                    events.append((-2, f"取消截止：{sub.name}",
                                   f"「{sub.name}」的取消截止日{when}到（{sub.cancel_by}）。"
                                   f"若要取消请在此之前操作。"))
            if sub.card_expiry:
                exp = _card_expiring(sub.card_expiry, today)
                if exp:
                    tail = f"（尾号 {sub.card_last4}）" if sub.card_last4 else ""
                    events.append((-3, f"付款卡将到期：{sub.name}",
                                   f"「{sub.name}」绑定的付款卡{tail}将于 {sub.card_expiry} 到期，"
                                   f"请及时更换，避免自动续费失败。"))
            for code, subject, body in events:
                if _already_sent(db, sub.id, code, today):
                    continue
                results = notify.dispatch(user, subject, body)
                ok_ch = [r["channel"] for r in results if r.get("ok")]
                db.add(NotificationLog(
                    subscription_id=sub.id, user_id=user.id, days_before=code,
                    channel=(ok_ch[0] if len(ok_ch) == 1 else f"multi:{len(ok_ch)}") if ok_ch else "none",
                    status="sent" if ok_ch else "failed", message=body,
                    sent_at=datetime.utcnow(),
                ))
                if ok_ch:
                    sent += 1
        db.commit()
    finally:
        db.close()
    return {"sent": sent}


def _card_expiring(mmyy: str, today: date) -> bool:
    """卡有效期 MM/YY，若在本月或下月到期则返回 True。"""
    try:
        mm, yy = mmyy.replace(" ", "").split("/")
        m, y = int(mm), 2000 + int(yy) if len(yy) == 2 else int(yy)
        exp_last = date(y + (1 if m == 12 else 0), 1 if m == 12 else m + 1, 1)
        # 到期月的月末 = 下月1号前一天
        from datetime import timedelta
        exp_last = exp_last - timedelta(days=1)
        days = (exp_last - today).days
        return 0 <= days <= 45
    except Exception:  # noqa: BLE001
        return False


def run_weekly_digest() -> dict:
    """每周汇总：把即将续费/已过期的订阅汇总成一条消息推送（按用户设置的星期几）。"""
    if database.SessionLocal is None:
        return {"sent": 0, "skipped": "数据库未配置"}
    today = date.today()
    weekday = today.weekday()  # 0=周一
    sent = 0
    db = database.SessionLocal()
    try:
        users = db.scalars(select(User).where(User.is_active.is_(True))).all()
        for user in users:
            st = user.notify_settings or {}
            if not st.get("digest_enabled"):
                continue
            if int(st.get("digest_weekday", 0)) != weekday:
                continue
            cfg = notify.load_config(user)
            if not any(cfg.get(c, {}).get("enabled") for c in notify.CHANNELS):
                continue
            subs = db.scalars(select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.is_active.is_(True),
                Subscription.billing_type == "recurring",
                Subscription.next_renewal_date.is_not(None),
            )).all()
            upcoming = sorted(
                [s for s in subs if 0 <= (s.next_renewal_date - today).days <= 30],
                key=lambda s: s.next_renewal_date,
            )
            overdue = [s for s in subs if (s.next_renewal_date - today).days < 0]
            if not upcoming and not overdue:
                continue
            lines = ["📅 *本周订阅汇总*", ""]
            if overdue:
                lines.append(f"⚠️ 已过期 {len(overdue)} 项：")
                for s in overdue[:10]:
                    lines.append(f"· {_escape_md(s.name)}（{s.next_renewal_date}）")
                lines.append("")
            if upcoming:
                lines.append(f"🔔 未来 30 天将续费 {len(upcoming)} 项：")
                for s in upcoming[:15]:
                    dleft = (s.next_renewal_date - today).days
                    lines.append(f"· {_escape_md(s.name)} — {s.next_renewal_date}（{dleft} 天，{s.amount:.2f} {s.currency}）")
            text_md = "\n".join(lines)
            notify.dispatch(user, "本周订阅汇总", _strip_md_local(text_md), text_md=text_md, event="digest")
            sent += 1
    finally:
        db.close()
    return {"sent": sent}


def _strip_md_local(text: str) -> str:
    return notify._strip_md(text)


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
    # 每天凌晨 3:30 自动整站备份到本地磁盘
    _scheduler.add_job(
        _auto_backup_job,
        CronTrigger(hour=3, minute=30),
        id="daily_auto_backup",
        replace_existing=True,
    )
    # 每天与提醒同一时间检查 试用/取消/卡到期
    _scheduler.add_job(
        run_date_reminders,
        CronTrigger(hour=hour, minute=minute),
        id="daily_date_reminders",
        replace_existing=True,
    )
    # 每天 08:00 检查是否到用户设定的每周汇总日
    _scheduler.add_job(
        run_weekly_digest,
        CronTrigger(hour=8, minute=0),
        id="weekly_digest",
        replace_existing=True,
    )
    _scheduler.start()


def _auto_backup_job() -> None:
    from app.services import autobackup  # 延迟导入避免循环依赖
    try:
        autobackup.run_auto_backup()
    except Exception:  # noqa: BLE001
        pass


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
