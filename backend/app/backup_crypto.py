"""Portable full-backup encryption; independent of the server JWT secret."""
import base64
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

FORMAT = "encrypted-full-v1"
MAX_BYTES = 64 * 1024 * 1024


def _key(password: str, salt: bytes) -> bytes:
    return PBKDF2HMAC(algorithm=SHA256(), length=32, salt=salt, iterations=310000).derive(password.encode())


def encrypt_backup(data: dict, password: str) -> dict:
    if len(password) < 12:
        raise ValueError("整站备份密码至少 12 位，请妥善保存")
    raw = json.dumps(data, ensure_ascii=False).encode()
    if len(raw) > MAX_BYTES:
        raise ValueError("整站备份超过 64 MB 上限")
    salt, iv = os.urandom(16), os.urandom(12)
    encrypted = AESGCM(_key(password, salt)).encrypt(iv, raw, FORMAT.encode())
    return {"app": "EasySub", "format": FORMAT, "users_count": len(data["users"]),
            **{k: base64.b64encode(v).decode() for k, v in (("salt", salt), ("iv", iv), ("ciphertext", encrypted))}}


def decrypt_backup(data: dict, password: str | None) -> dict:
    if data.get("format") != FORMAT or not password:
        raise ValueError("请填写整站备份密码，或检查文件格式")
    try:
        if not isinstance(data.get("ciphertext"), str) or len(data["ciphertext"]) > (MAX_BYTES + 16) * 4 // 3 + 4:
            raise ValueError()
        salt, iv, ciphertext = (base64.b64decode(data[k], validate=True) for k in ("salt", "iv", "ciphertext"))
        if len(salt) != 16 or len(iv) != 12:
            raise ValueError()
        return json.loads(AESGCM(_key(password, salt)).decrypt(iv, ciphertext, FORMAT.encode()))
    except Exception as exc:
        raise ValueError("密码错误或备份文件损坏，原数据未更改") from exc
