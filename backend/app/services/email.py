"""邮件服务（SMTP）：发送注册验证码。

若未配置 SMTP，则视为“无需邮箱验证”，注册时直接通过邮箱验证环节
（仍需管理员审核，由 require_admin_approval 控制）。
"""
import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings


def smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from)


def _send(to_email: str, subject: str, body: str) -> None:
    if not smtp_configured():
        raise RuntimeError("未配置 SMTP")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(body)
    _deliver(msg)


def send_reset(to_email: str, code: str) -> None:
    _send(
        to_email, "省心订阅 EasySub — 密码重置码",
        f"你好，\n\n你的密码重置码是：{code}\n\n"
        f"该验证码 15 分钟内有效。如果不是你本人操作，请忽略此邮件并注意账号安全。\n\n— 省心订阅 EasySub",
    )


def send_code(to_email: str, code: str) -> None:
    if not smtp_configured():
        raise RuntimeError("未配置 SMTP")
    msg = EmailMessage()
    msg["Subject"] = "省心订阅 EasySub — 注册验证码"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(
        f"你好，\n\n你的注册验证码是：{code}\n\n"
        f"该验证码 10 分钟内有效。如果不是你本人操作，请忽略此邮件。\n\n— 省心订阅 EasySub"
    )
    _deliver(msg)


def _deliver(msg: EmailMessage) -> None:
    if settings.smtp_tls:
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as s:
            s.starttls(context=context)
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
    else:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as s:
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
