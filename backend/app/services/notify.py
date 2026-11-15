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

from app import crypto, outbound
from app.services import telegram

# 各渠道需加密存储的敏感字段
_SECRET_FIELDS = {
    "telegram": ["bot_token"], "feishu": ["app_secret"], "qq": ["app_secret"],
    "email": ["password"], "pushplus": ["token"], "serverchan": ["sendkey"],
    "wecom": ["secret"],
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
    # 企业微信：mode=webhook 群机器人；mode=app 自建应用（企业ID+应用ID+Secret，可走 API 代理）
    "wecom": {"enabled": False, "mode": "webhook", "url": "",
              "corp_id": "", "agent_id": "", "secret": "", "proxy_base": "",
              "to_user": "@all", "to_party": "", "to_tag": "",
              "msg_type": "text", "card_url": ""},
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
    with outbound.client(timeout=15) as c:
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
    with outbound.client(timeout=15) as c:
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
    with outbound.client(timeout=15) as c:
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
        with outbound.CheckedSMTPSSL(host, port, timeout=20, context=ctx) as s:
            if user:
                s.login(user, pwd)
            s.send_message(msg)
    else:
        with outbound.CheckedSMTP(host, port, timeout=20) as s:
            s.starttls(context=ssl.create_default_context())
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
    with outbound.client(timeout=15) as c:
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
                with outbound.client(timeout=timeout) as c:
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
    with outbound.client(timeout=15) as c:
        r = c.post(f"https://sctapi.ftqq.com/{key}.send",
                   data={"title": subject or "省心订阅 EasySub", "desp": text})
        r.raise_for_status()
        if r.json().get("code", 0) != 0:
            raise RuntimeError(f"Server酱发送失败：{r.text}")


# ---- 企业微信（群机器人 / 自建应用） --------------------------------------- #
WECOM_DEFAULT_BASE = "https://qyapi.weixin.qq.com"
# 自建应用的 access_token 缓存：key -> (token, 过期时间戳)。企业微信对 gettoken 有频率限制，
# 且同一 Secret 重复获取会顶掉旧 token，因此必须缓存复用（官方有效期 7200s）。
_WECOM_TOKENS: dict[str, tuple[str, float]] = {}
# 需要重新获取 token 的错误码：40014 不合法的 access_token / 42001 已过期 / 41001 缺少 token
_WECOM_TOKEN_ERRS = {40014, 42001, 41001}


def _trunc_bytes(text: str, limit: int) -> str:
    """按 UTF-8 字节数截断（企业微信 text 上限 2048B、markdown 4096B、textcard 描述 512B）。"""
    raw = (text or "").encode("utf-8")
    if len(raw) <= limit:
        return text or ""
    return raw[: limit - 3].decode("utf-8", "ignore") + "..."


def wecom_api_base(conf: dict) -> str:
    """API 代理地址；留空用官方域名。容忍用户把 /cgi-bin 一起粘进来。"""
    base = (conf.get("proxy_base") or "").strip().rstrip("/")
    if not base:
        return WECOM_DEFAULT_BASE
    if not base.startswith(("http://", "https://")):
        base = "https://" + base
    if base.endswith("/cgi-bin"):
        base = base[: -len("/cgi-bin")]
    return base


def wecom_token(conf: dict, force: bool = False) -> str:
    """获取（并缓存）自建应用 access_token。"""
    corp_id = (conf.get("corp_id") or "").strip()
    secret = (conf.get("secret") or "").strip()
    if not corp_id or not secret:
        raise RuntimeError("企业微信自建应用未配置企业ID / 应用Secret")
    base = wecom_api_base(conf)
    key = f"{base}|{corp_id}|{hashlib.sha256(secret.encode()).hexdigest()[:16]}"
    hit = _WECOM_TOKENS.get(key)
    if hit and not force and hit[1] > time.time():
        return hit[0]
    with outbound.client(timeout=15) as c:
        r = c.get(f"{base}/cgi-bin/gettoken",
                  params={"corpid": corp_id, "corpsecret": secret})
        r.raise_for_status()
        data = r.json()
    token = data.get("access_token")
    if data.get("errcode", 0) != 0 or not token:
        raise RuntimeError(
            f"企业微信获取 access_token 失败：{data.get('errcode')} {data.get('errmsg')}"
            "（请检查企业ID / 应用Secret，以及是否已在「企业可信IP」放行服务器出口 IP）"
        )
    ttl = int(data.get("expires_in") or 7200)
    _WECOM_TOKENS[key] = (token, time.time() + max(60, ttl - 200))  # 提前 200s 续期
    return token


def wecom_agent_info(conf: dict) -> dict:
    """读取自建应用信息（校验配置用）：返回应用名、可见范围人数等。"""
    agent_id = str(conf.get("agent_id") or "").strip()
    if not agent_id:
        raise RuntimeError("企业微信自建应用未配置应用ID（AgentId）")
    base = wecom_api_base(conf)
    for attempt in (0, 1):
        token = wecom_token(conf, force=bool(attempt))
        with outbound.client(timeout=15) as c:
            r = c.get(f"{base}/cgi-bin/agent/get",
                      params={"access_token": token, "agentid": agent_id})
            r.raise_for_status()
            data = r.json()
        code = data.get("errcode", 0)
        if code in _WECOM_TOKEN_ERRS and attempt == 0:
            continue
        if code != 0:
            raise RuntimeError(f"企业微信读取应用失败：{code} {data.get('errmsg')}")
        allow = data.get("allow_userinfos") or {}
        return {
            "agentid": data.get("agentid"),
            "name": data.get("name"),
            "square_logo_url": data.get("square_logo_url"),
            "users": len(allow.get("user") or []),
            "parties": len((data.get("allow_partys") or {}).get("partyid") or []),
            "tags": len((data.get("allow_tags") or {}).get("tagid") or []),
        }
    raise RuntimeError("企业微信读取应用失败：access_token 反复失效")


def _wecom_payload(conf: dict, subject: str, text: str) -> dict:
    """按消息类型构造消息体（text / markdown / textcard）。"""
    msg_type = (conf.get("msg_type") or "text").strip()
    body_text = f"{subject}\n\n{text}" if subject else text
    if msg_type == "markdown":
        return {"msgtype": "markdown",
                "markdown": {"content": _trunc_bytes(body_text, 4096)}}
    if msg_type == "textcard":
        return {"msgtype": "textcard", "textcard": {
            "title": _trunc_bytes(subject or "省心订阅 EasySub", 128),
            "description": _trunc_bytes(text, 512),
            "url": conf.get("card_url") or "https://github.com/suyijun8182/easysub",
            "btntxt": "查看详情",
        }}
    return {"msgtype": "text", "text": {"content": _trunc_bytes(body_text, 2048)}}


def _send_wecom_robot(conf: dict, subject: str, text: str) -> None:
    """群机器人 Webhook 模式。"""
    url = (conf.get("url") or "").strip()
    if not url:
        raise RuntimeError("企业微信未配置群机器人 Webhook")
    payload = _wecom_payload(conf, subject, text)
    if payload["msgtype"] == "textcard":  # 群机器人不支持 textcard，降级为 text
        payload = {"msgtype": "text",
                   "text": {"content": _trunc_bytes(f"{subject}\n\n{text}" if subject else text, 2048)}}
    with outbound.client(timeout=15) as c:
        r = c.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        if data.get("errcode", 0) != 0:
            raise RuntimeError(f"企业微信群机器人发送失败：{data.get('errcode')} {data.get('errmsg')}")


def _send_wecom_app(conf: dict, subject: str, text: str) -> None:
    """自建应用模式（企业ID + 应用ID + Secret），与 CMSHelp「企业微信配置」一致。"""
    agent_id = str(conf.get("agent_id") or "").strip()
    if not agent_id:
        raise RuntimeError("企业微信自建应用未配置应用ID（AgentId）")
    to_user = (conf.get("to_user") or "").strip()
    to_party = (conf.get("to_party") or "").strip()
    to_tag = (conf.get("to_tag") or "").strip()
    if not (to_user or to_party or to_tag):
        to_user = "@all"  # 三者全空则发给应用可见范围内全部成员
    payload = _wecom_payload(conf, subject, text)
    payload.update({"touser": to_user, "toparty": to_party, "totag": to_tag,
                    "agentid": int(agent_id) if agent_id.isdigit() else agent_id,
                    "safe": 0, "enable_duplicate_check": 0})
    base = wecom_api_base(conf)
    for attempt in (0, 1):  # token 失效时强制刷新重试一次
        token = wecom_token(conf, force=bool(attempt))
        with outbound.client(timeout=15) as c:
            r = c.post(f"{base}/cgi-bin/message/send",
                       params={"access_token": token}, json=payload)
            r.raise_for_status()
            data = r.json()
        code = data.get("errcode", 0)
        if code in _WECOM_TOKEN_ERRS and attempt == 0:
            continue
        if code != 0:
            hint = ""
            if code == 81013:
                hint = "（接收人不在应用可见范围内，请到「应用管理→可见范围」添加成员）"
            elif code in (60020, 301014):
                hint = "（服务器 IP 未在「企业可信IP」白名单中，或需要配置 API 代理）"
            elif code == 40056:
                hint = "（应用ID AgentId 不正确）"
            raise RuntimeError(f"企业微信发送失败：{code} {data.get('errmsg')}{hint}")
        # errcode=0 但接收人被剔除时，消息实际没人收到，需要报错而不是假装成功
        invalid = [str(data.get(k) or "").strip("| ") for k in
                   ("invaliduser", "invalidparty", "invalidtag")]
        invalid = [v for v in invalid if v]
        if invalid:
            raise RuntimeError(
                f"企业微信部分接收人无效：{' / '.join(invalid)}"
                "（请核对成员 UserID，并确认其在应用可见范围内）"
            )
        return


def _send_wecom(conf: dict, subject: str, text: str) -> None:
    if (conf.get("mode") or "webhook") == "app":
        _send_wecom_app(conf, subject, text)
    else:
        _send_wecom_robot(conf, subject, text)


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
    with outbound.client(timeout=15) as c:
        r = c.post(url, json={"msgtype": "text", "text": {"content": body_text}})
        r.raise_for_status()
        if r.json().get("errcode", 0) != 0:
            raise RuntimeError(f"钉钉发送失败：{r.text}")


def _send_discord(conf: dict, subject: str, text: str) -> None:
    url = conf.get("url")
    if not url:
        raise RuntimeError("Discord 未配置 Webhook URL")
    content = f"**{subject}**\n{text}" if subject else text
    with outbound.client(timeout=15) as c:
        c.post(url, json={"content": content[:1900]}).raise_for_status()


def _send_slack(conf: dict, subject: str, text: str) -> None:
    url = conf.get("url")
    if not url:
        raise RuntimeError("Slack 未配置 Webhook URL")
    body_text = f"*{subject}*\n{text}" if subject else text
    with outbound.client(timeout=15) as c:
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
    with outbound.client(timeout=15) as c:
        c.post(f"{server}/{topic}", content=body.encode("utf-8"), headers=headers).raise_for_status()


def _send_gotify(conf: dict, subject: str, text: str) -> None:
    server = (conf.get("server") or "").rstrip("/")
    token = conf.get("token")
    if not server or not token:
        raise RuntimeError("Gotify 未配置 Server / Token")
    with outbound.client(timeout=15) as c:
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
    outbound.validate_config(channel, conf)
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
             event: str = "reminder", only_channels: set[str] | None = None) -> list[dict]:
    """向该用户所有已启用渠道推送。返回每个渠道的结果列表。"""
    cfg = load_config(user)
    results: list[dict] = []
    for channel in CHANNELS:
        if only_channels is not None and channel not in only_channels:
            continue
        conf = cfg.get(channel, {})
        if not conf.get("enabled"):
            continue
        try:
            outbound.validate_config(channel, conf)
            if channel == "telegram":
                _send_telegram(conf, subject, text_md or text_plain)
            elif channel == "webhook":
                _send_webhook(conf, subject, text_plain, event=event)
            else:
                _SENDERS[channel](conf, subject, text_plain)
            results.append({"channel": channel, "ok": True})
        except Exception as e:  # noqa: BLE001
            results.append({"channel": channel, "ok": False, "error": f"{type(e).__name__}: 通知发送失败，请检查地址、白名单或渠道配置"})
    return results
