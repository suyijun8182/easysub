"""敏感信息的可逆加密（存库前加密，读取时解密），密钥由 JWT_SECRET 派生。

设计要点：
- 向后兼容：历史明文（无 "enc:" 前缀）原样返回，升级后首次保存才写成密文，不丢数据。
- 失败软化：若密钥变更导致解密失败，返回空串而非抛异常，避免影响功能（用户重填即可）。
已知示例密钥加密的数据兼容读取，并在启动迁移或下次保存时换用当前密钥。
轮换自定义 JWT_SECRET 后，旧数据仍需使用原密钥恢复。
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings
from app.secrets_store import INSECURE_SECRETS

_PREFIX = "enc:"


def _fernet(secret: str | None = None) -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256((settings.jwt_secret if secret is None else secret).encode()).digest())
    return Fernet(key)


def _legacy_plaintext(value: str) -> str | None:
    for secret in sorted(INSECURE_SECRETS | {"easysub"}):
        try:
            return _fernet(secret).decrypt(value[len(_PREFIX):].encode()).decode()
        except (InvalidToken, ValueError):
            continue
    return None


def encrypt(value: str | None) -> str | None:
    if not value:
        return value
    if value.startswith(_PREFIX):
        try:
            _fernet().decrypt(value[len(_PREFIX):].encode())
            return value
        except (InvalidToken, ValueError):
            plaintext = _legacy_plaintext(value)
            if plaintext is None:
                return value  # Unknown keys must not destroy existing ciphertext.
            value = plaintext
    token = _fernet().encrypt(value.encode()).decode()
    return _PREFIX + token


def decrypt(value: str | None) -> str | None:
    if not value or not value.startswith(_PREFIX):
        return value  # 明文或空，原样返回（向后兼容）
    try:
        return _fernet().decrypt(value[len(_PREFIX):].encode()).decode()
    except (InvalidToken, ValueError):
        plaintext = _legacy_plaintext(value)
        return plaintext if plaintext is not None else ""
