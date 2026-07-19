"""统一多渠道通知服务。

在 Telegram 之外新增：飞书 Bot / QQ Bot / Bark / Email / Pushplus / Webhook。
每个用户的渠道配置保存在 users.notify_config（JSON）中；Telegram 为兼容旧版，
未写入 notify_config 时回退读取旧的 telegram_* 列。

对外主要接口：
- default_config()            返回全部渠道的默认结构
- load_config(user)           读取某用户完整配置（含旧列回退）
- apply_config(user, cfg)     把配置写回 user（并同步 telegram 旧列以兼容）
- dispatch(user, subject, text_plain, text_md=None)  向所有已启用渠道推送
- send_one(channel, conf, subject, text)             按单渠道配置发送（用于测试）
"""
import base64
import copy
import hashlib
import hmac
import json
import re
import smtplib
import ssl
import time
import urllib.parse
from email.message import EmailMessage

import httpx

from app import crypto
from app.services import telegram

# 各渠道需加密存储的敏感字段
_SECRET_FIELDS = {
    "telegram": ["bot_token"], "feishu": ["app_secret"], "qq": ["app_secret"],
    "email": ["password"], "pushplus": ["token"], "serverchan": ["sendkey"],
    "dingtalk": ["secret"], "ntfy": ["token"], "gotify": ["token"], "webhook": ["secret"],
}

# ---- 渠道默认配置 ---------------------------------------------------------- #
_DEFAULTS = {
    "telegram": {"enabled": False, "bot_token": "", "chat_id": "", "admin_id": "",
                 "api_base": "", "proxy": ""},
    "feishu": {"enabled": False, "app_id": "", "app_secret": "", "chat_ids": ""},
    "qq": {"enabled": False, "app_id": "", "app_secret": "", "group_ids": "", "user_ids": ""},
    "bark": {"enabled": False, "urls": [], "group": "", "level": "active", "icon": ""},
    "email": {"enabled": False, "host": "", "port": 465, "ssl": True, "username": "",
              "password": "", "from": "", "to": ""},
    "pushplus": {"enabled": False, "token": "", "topic": "", "channel": "wechat"},
    "serverchan": {"enabled": False, "sendkey": ""},
    "wecom": {"enabled": False, "url": ""},
    "dingtalk": {"enabled": False, "url": "", "secret": ""},
    "discord": {"enabled": False, "url": ""},
    "slack": {"enabled": False, "url": ""},
    "ntfy": {"enabled": False, "server": "https://ntfy.sh", "topic": "", "token": ""},
    "gotify": {"enabled": False, "server": "", "token": "", "priority": 5},
    "webhook": {"enabled": False, "urls": [], "secret": "", "headers": [], "template": "",
                "timeout_ms": 5000, "max_retries": 3},
}

CHANNELS = list(_DEFAULTS.keys())


def default_config() -> dict:
    return copy.deepcopy(_DEFAULTS)


def load_config(user) -> dict:
    cfg = default_config()
    saved = user.notify_config or {}
    for key, sub in saved.items():
        if key in cfg and isinstance(sub, dict):
            cfg[key].update({k: v for k, v in sub.items() if k in cfg[key]})
    # 解密敏感字段（历史明文原样返回）
    for ch, fields in _SECRET_FIELDS.items():
        for f in fields:
            if cfg.get(ch, {}).get(f):
                cfg[ch][f] = crypto.decrypt(cfg[ch][f])
    # 兼容旧版：telegram 尚未存入 notify_config 时用旧列回填
    if not (isinstance(saved, dict) and saved.get("telegram")):
        cfg["telegram"].update({
            "enabled": bool(getattr(user, "telegram_enabled", False)),
            "bot_token": getattr(user, "telegram_bot_token", "") or "",
            "chat_id": getattr(user, "telegram_chat_id", "") or "",
            "admin_id": getattr(user, "telegram_admin_id", "") or "",
            "api_base": getattr(user, "telegram_api_base", "") or "",
            "proxy": getattr(user, "telegram_proxy", "") or "",
        })
    return cfg


def apply_config(user, incoming: dict) -> dict:
    """把前端提交的配置合并进默认结构后写回 user.notify_config，返回规范化后的配置。"""
    cfg = default_config()
    for key, sub in (incoming or {}).items():
        if key in cfg and isinstance(sub, dict):
            cfg[key].update({k: v for k, v in sub.items() if k in cfg[key]})
    # 同步 telegram 到旧列（保持明文，验证机器人/测试等旧路径直接可用）
    tg = cfg["telegram"]
    user.telegram_enabled = bool(tg.get("enabled"))
    user.telegram_bot_token = tg.get("bot_token") or None
    user.telegram_chat_id = tg.get("chat_id") or None
    user.telegram_admin_id = tg.get("admin_id") or None
    user.telegram_api_base = tg.get("api_base") or None
    user.telegram_proxy = tg.get("proxy") or None
    # 敏感字段加密后再写入 notify_config
    stored = copy.deepcopy(cfg)
    for ch, fields in _SECRET_FIELDS.items():
        for f in fields:
            if stored.get(ch, {}).get(f):
                stored[ch][f] = crypto.encrypt(stored[ch][f])
    user.notify_config = stored
    return cfg


# ---- 文本处理 -------------------------------------------------------------- #
def _strip_md(text: str) -> str:
    """去掉 Markdown 强调符号，供不支持 Markdown 的渠道使用。"""
    if not text:
        return ""
    text = text.replace("\\*", "*").replace("\\_", "_").replace("\\`", "`").replace("\\[", "[")
    return re.sub(r"[*_`]", "", text)


def _split(csv: str) -> list[str]:
    return [x.strip() for x in (csv or "").replace("，", ",").split(",") if x.strip()]


# ---- 各渠道发送实现（失败抛异常） ------------------------------------------ #
def _send_telegram(conf: dict, subject: str, text: str) -> None:
    token = conf.get("bot_token")
    chat_id = conf.get("chat_id")
    if not token or not chat_id:
        raise RuntimeError("Telegram 未配置 Bot Token 或 Chat ID")
    telegram.send_message(
        chat_id, text, token=token,
        api_base=conf.get("api_base") or None, proxy=conf.get("proxy") or None,
    )


def _send_feishu(conf: dict, subject: str, text: str) -> None:
    app_id, secret = conf.get("app_id"), conf.get("app_secret")
    chat_ids = _split(conf.get("chat_ids", ""))
    if not app_id or not secret or not chat_ids:
        raise RuntimeError("飞书未配置 App ID / Secret / Chat IDs")
    with httpx.Client(timeout=15) as c:
        r = c.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": secret},
        )
        r.raise_for_status()
        token = r.json().get("tenant_access_token")
        if not token:
            raise RuntimeError(f"飞书获取 token 失败：{r.text}")
        body_text = f"{subject}\n\n{text}" if subject else text
        for cid in chat_ids:
            resp = c.post(
                "https://open.feishu.cn/open-apis/im/v1/messages",
                params={"receive_id_type": "chat_id"},
                headers={"Authorization": f"Bearer {token}"},
                json={"receive_id": cid, "msg_type": "text",
                      "content": json.dumps({"text": body_text}, ensure_ascii=False)},
            )
            data = resp.json()
            if data.get("code", 0) != 0:
                raise RuntimeError(f"飞书发送失败（{cid}）：{data.get('msg')}")


def _send_qq(conf: dict, subject: str, text: str) -> None:
    app_id, secret = conf.get("app_id"), conf.get("app_secret")
    groups = _split(conf.get("group_ids", ""))
    users = _split(conf.get("user_ids", ""))
    if not app_id or not secret:
        raise RuntimeError("QQ 未配置 App ID / Secret")
    if not groups and not users:
        raise RuntimeError("QQ 未填写任何群聊或私聊 OpenID")
    body_text = f"{subject}\n\n{text}" if subject else text
    with httpx.Client(timeout=15) as c:
        r = c.post("https://bots.qq.com/app/getAppAccessToken",
                   json={"appId": app_id, "clientSecret": secret})
        r.raise_for_status()
        token = r.json().get("access_token")
        if not token:
            raise RuntimeError(f"QQ 获取 access_token 失败：{r.text}")
        headers = {"Authorization": f"QQBot {token}", "Content-Type": "application/json"}
        for gid in groups:
            resp = c.post(f"https://api.sgroup.qq.com/v2/groups/{gid}/messages",
                          headers=headers, json={"content": body_text, "msg_type": 0})
            if resp.status_code >= 300:
                raise RuntimeError(f"QQ 群 {gid} 发送失败：{resp.text}")
        for uid in users:
            resp = c.post(f"https://api.sgroup.qq.com/v2/users/{uid}/messages",
                          headers=headers, json={"content": body_text, "msg_type": 0})
            if resp.status_code >= 300:
                raise RuntimeError(f"QQ 用户 {uid} 发送失败：{resp.text}")


def _send_bark(conf: dict, subject: str, text: str) -> None:
    urls = [u for u in (conf.get("urls") or []) if u]
    if not urls:
        raise RuntimeError("Bark 未配置任何目标 URL")
    payload = {"title": subject or "省心订阅 EasySub", "body": text}
    if conf.get("group"):
        payload["group"] = conf["group"]
    if conf.get("level"):
        payload["level"] = conf["level"]
    if conf.get("icon"):
        payload["icon"] = conf["icon"]
    with httpx.Client(timeout=15) as c:
        for url in urls:
            resp = c.post(url.rstrip("/"), json=payload)
            resp.raise_for_status()
            if resp.json().get("code", 200) not in (200, 0):
                raise RuntimeError(f"Bark 推送失败：{resp.text}")


def _send_email(conf: dict, subject: str, text: str) -> None:
    host = conf.get("host")
    to_list = _split(conf.get("to", ""))
    sender = conf.get("from") or conf.get("username")
    if not host or not to_list or not sender:
        raise RuntimeError("Email 未配置 SMTP 主机 / 发件人 / 收件人")
    port = int(conf.get("port") or (465 if conf.get("ssl") else 587))
    msg = EmailMessage()
    msg["Subject"] = subject or "省心订阅 EasySub 通知"
    msg["From"] = sender
    msg["To"] = ", ".join(to_list)
    msg.set_content(text)
    user, pwd = conf.get("username"), conf.get("password")
    if conf.get("ssl"):
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, timeout=20, context=ctx) as s:
            if user:
                s.login(user, pwd)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=20) as s:
            try:
                s.starttls(context=ssl.create_default_context())
            except smtplib.SMTPException:
                pass
            if user:
                s.login(user, pwd)
            s.send_message(msg)


def _send_pushplus(conf: dict, subject: str, text: str) -> None:
    token = conf.get("token")
    if not token:
        raise RuntimeError("Pushplus 未配置 Token")
    body = {"token": token, "title": subject or "省心订阅 EasySub 通知",
            "content": text, "template": "txt"}
    if conf.get("topic"):
        body["topic"] = conf["topic"]
    if conf.get("channel"):
        body["channel"] = conf["channel"]
    with httpx.Client(timeout=15) as c:
        resp = c.post("https://www.pushplus.plus/send", json=body)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 200:
            raise RuntimeError(f"Pushplus 发送失败：{data.get('msg')}")


def _render_template(tpl: str, ctx: dict) -> str:
    def repl(m):
        return str(ctx.get(m.group(1).strip(), m.group(0)))
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", repl, tpl)


def _send_webhook(conf: dict, subject: str, text: str, event: str = "reminder") -> None:
    urls = [u for u in (conf.get("urls") or []) if u]
    if not urls:
        raise RuntimeError("Webhook 未配置任何目标 URL")
    ts = int(time.time())
    ctx = {"text": text, "subject": subject, "event": event, "timestamp": ts}
    rendered = _render_template(conf["template"], ctx) if conf.get("template") else text
    payload = {"text": rendered, "subject": subject, "event": event, "timestamp": ts}
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    for h in conf.get("headers") or []:
        k, v = (h.get("key"), h.get("value")) if isinstance(h, dict) else (None, None)
        if k and k.lower() not in ("content-type", "x-easysub-signature"):
            headers[k] = v
    if conf.get("secret"):
        sig = hmac.new(conf["secret"].encode(), raw, hashlib.sha256).hexdigest()
        headers["X-EasySub-Signature"] = sig

    timeout = max(1, int(conf.get("timeout_ms") or 5000)) / 1000
    retries = max(0, int(conf.get("max_retries") or 0))
    last_err = None
    for url in urls:
        for attempt in range(retries + 1):
            try:
                with httpx.Client(timeout=timeout) as c:
                    resp = c.post(url, content=raw, headers=headers)
                    resp.raise_for_status()
                last_err = None
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
        if last_err:
            raise RuntimeError(f"Webhook 发送失败（{url}）：{last_err}")


def _send_serverchan(conf: dict, subject: str, text: str) -> None:
    key = conf.get("sendkey")
    if not key:
        raise RuntimeError("Server酱未配置 SendKey")
    with httpx.Client(timeout=15) as c:
        r = c.post(f"https://sctapi.ftqq.com/{key}.send",
                   data={"title": subject or "省心订阅 EasySub", "desp": text})
        r.raise_for_status()
        if r.json().get("code", 0) != 0:
            raise RuntimeError(f"Server酱发送失败：{r.text}")


def _send_wecom(conf: dict, subject: str, text: str) -> None:
    url = conf.get("url")
    if not url:
        raise RuntimeError("企业微信未配置机器人 Webhook")
    body_text = f"{subject}\n\n{text}" if subject else text
    with httpx.Client(timeout=15) as c:
        r = c.post(url, json={"msgtype": "text", "text": {"content": body_text}})
        r.raise_for_status()
        if r.json().get("errcode", 0) != 0:
            raise RuntimeError(f"企业微信发送失败：{r.text}")


def _send_dingtalk(conf: dict, subject: str, text: str) -> None:
    url = conf.get("url")
    if not url:
        raise RuntimeError("钉钉未配置机器人 Webhook")
    secret = conf.get("secret")
    if secret:
        ts = str(round(time.time() * 1000))
        sign = urllib.parse.quote_plus(base64.b64encode(
            hmac.new(secret.encode(), f"{ts}\n{secret}".encode(), hashlib.sha256).digest()
        ))
        url = f"{url}&timestamp={ts}&sign={sign}"
    body_text = f"{subject}\n\n{text}" if subject else text
    with httpx.Client(timeout=15) as c:
        r = c.post(url, json={"msgtype": "text", "text": {"content": body_text}})
        r.raise_for_status()
        if r.json().get("errcode", 0) != 0:
            raise RuntimeError(f"钉钉发送失败：{r.text}")


def _send_discord(conf: dict, subject: str, text: str) -> None:
    url = conf.get("url")
    if not url:
        raise RuntimeError("Discord 未配置 Webhook URL")
    content = f"**{subject}**\n{text}" if subject else text
    with httpx.Client(timeout=15) as c:
        c.post(url, json={"content": content[:1900]}).raise_for_status()


def _send_slack(conf: dict, subject: str, text: str) -> None:
    url = conf.get("url")
    if not url:
        raise RuntimeError("Slack 未配置 Webhook URL")
    body_text = f"*{subject}*\n{text}" if subject else text
    with httpx.Client(timeout=15) as c:
        c.post(url, json={"text": body_text}).raise_for_status()


def _send_ntfy(conf: dict, subject: str, text: str) -> None:
    server = (conf.get("server") or "https://ntfy.sh").rstrip("/")
    topic = conf.get("topic")
    if not topic:
        raise RuntimeError("ntfy 未配置 Topic")
    body = f"{subject}\n\n{text}" if subject else text
    headers = {}
    if conf.get("token"):
        headers["Authorization"] = f"Bearer {conf['token']}"
    with httpx.Client(timeout=15) as c:
        c.post(f"{server}/{topic}", content=body.encode("utf-8"), headers=headers).raise_for_status()


def _send_gotify(conf: dict, subject: str, text: str) -> None:
    server = (conf.get("server") or "").rstrip("/")
    token = conf.get("token")
    if not server or not token:
        raise RuntimeError("Gotify 未配置 Server / Token")
    with httpx.Client(timeout=15) as c:
        c.post(f"{server}/message", params={"token": token},
               json={"title": subject or "省心订阅 EasySub", "message": text,
                     "priority": int(conf.get("priority") or 5)}).raise_for_status()


_SENDERS = {
    "telegram": _send_telegram,
    "feishu": _send_feishu,
    "qq": _send_qq,
    "bark": _send_bark,
    "email": _send_email,
    "pushplus": _send_pushplus,
    "serverchan": _send_serverchan,
    "wecom": _send_wecom,
    "dingtalk": _send_dingtalk,
    "discord": _send_discord,
    "slack": _send_slack,
    "ntfy": _send_ntfy,
    "gotify": _send_gotify,
    "webhook": _send_webhook,
}


def send_one(channel: str, conf: dict, subject: str, text: str) -> None:
    """按单个渠道配置发送（供测试按钮使用）。失败抛异常。"""
    fn = _SENDERS.get(channel)
    if not fn:
        raise RuntimeError(f"未知渠道：{channel}")
    # 非 Telegram 渠道用纯文本
    body = text if channel == "telegram" else _strip_md(text)
    fn(conf, subject, body)


def in_quiet_hours(user) -> bool:
    """当前本地时间是否落在用户设置的免打扰时段内。支持跨午夜（如 23:00-07:00）。"""
    st = getattr(user, "notify_settings", None) or {}
    q1, q2 = st.get("quiet_start"), st.get("quiet_end")
    if not q1 or not q2:
        return False
    now = time.strftime("%H:%M")
    if q1 <= q2:
        return q1 <= now < q2
    return now >= q1 or now < q2  # 跨午夜窗口


def dispatch(user, subject: str, text_plain: str, text_md: str | None = None,
             event: str = "reminder") -> list[dict]:
    """向该用户所有已启用渠道推送。返回每个渠道的结果列表。"""
    cfg = load_config(user)
    results: list[dict] = []
    for channel in CHANNELS:
        conf = cfg.get(channel, {})
        if not conf.get("enabled"):
            continue
        try:
            if channel == "telegram":
                _send_telegram(conf, subject, text_md or text_plain)
            elif channel == "webhook":
                _send_webhook(conf, subject, text_plain, event=event)
            else:
                _SENDERS[channel](conf, subject, text_plain)
            results.append({"channel": channel, "ok": True})
        except Exception as e:  # noqa: BLE001
            results.append({"channel": channel, "ok": False, "error": f"{type(e).__name__}: {e}"})
    return results
