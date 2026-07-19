"""敏感信息的可逆加密（存库前加密，读取时解密），密钥由 JWT_SECRET 派生。

设计要点：
- 向后兼容：历史明文（无 "enc:" 前缀）原样返回，升级后首次保存才写成密文，不丢数据。
- 失败软化：若密钥变更导致解密失败，返回空串而非抛异常，避免影响功能（用户重填即可）。
注意：轮换 JWT_SECRET 会使已加密的密钥无法解密（需在网页重新填写），这是安全权衡。
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

_PREFIX = "enc:"


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256((settings.jwt_secret or "easysub").encode()).digest())
    return Fernet(key)


def encrypt(value: str | None) -> str | None:
    if not value:
        return value
    if value.startswith(_PREFIX):
        return value  # 已是密文
    token = _fernet().encrypt(value.encode()).decode()
    return _PREFIX + token


def decrypt(value: str | None) -> str | None:
    if not value or not value.startswith(_PREFIX):
        return value  # 明文或空，原样返回（向后兼容）
    try:
        return _fernet().decrypt(value[len(_PREFIX):].encode()).decode()
    except (InvalidToken, ValueError):
        return ""  # 解密失败（如密钥已轮换）：软化为空，避免报错
