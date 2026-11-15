"""Persist an installation-specific signing secret and migrate legacy ciphertext."""
import copy
import os
import secrets
from pathlib import Path

INSECURE_SECRETS = {
    "", "change-me", "change-me-to-a-long-random-secret",
    "please-change-this-to-a-random-secret", "change-me-to-a-random-secret",
}


def resolve_jwt_secret(configured: str) -> str:
    if configured not in INSECURE_SECRETS:
        return configured
    path = Path("data/jwt_secret")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        secret = path.read_text(encoding="utf-8").strip()
    else:
        secret = secrets.token_hex(32)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(secret)
    if secret in INSECURE_SECRETS:
        raise ValueError("data/jwt_secret contains an invalid signing secret")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    print("[security] JWT_SECRET 未设置或为示例值，已自动生成并保存到 data/jwt_secret")
    return secret


def reencrypt_legacy_secrets(db) -> None:
    from sqlalchemy import select, update
    from app import crypto
    from app.models import User, SyncRecord, SyncChange, SyncReceipt
    from app.services.notify import _SECRET_FIELDS

    # Core updates avoid publishing business changes into the sync journal.
    for row in db.execute(select(User.id, User.notify_config)):
        cfg = copy.deepcopy(row.notify_config)
        if not isinstance(cfg, dict):
            continue
        for channel, fields in _SECRET_FIELDS.items():
            if not isinstance(cfg.get(channel), dict):
                continue
            for field in fields:
                value = cfg[channel].get(field)
                if isinstance(value, str) and value.startswith("enc:"):
                    cfg[channel][field] = crypto.encrypt(value)
        if cfg != row.notify_config:
            db.execute(update(User.__table__).where(User.id == row.id).values(notify_config=cfg))
    for model in (SyncRecord, SyncChange, SyncReceipt):
        table = model.__table__
        for row in db.execute(select(table)).mappings():
            value = row["payload"]
            if not value.startswith("enc:"):
                continue
            rotated = crypto.encrypt(value)
            if rotated != value:
                condition = [column == row[column.name] for column in table.primary_key]
                db.execute(update(table).where(*condition).values(payload=rotated))
    db.commit()


def rotate_legacy_secrets_safely(db) -> None:
    """Startup wrapper: a bad row must never make the database look unavailable."""
    try:
        reencrypt_legacy_secrets(db)
    except Exception as exc:  # noqa: BLE001
        # Legacy ciphertext stays readable through crypto's fallback keys; retry next start.
        db.rollback()
        print(f"[security] 旧密文重新加密失败，已跳过：{type(exc).__name__}")
