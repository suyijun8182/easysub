"""定时自动备份：每天把整站数据导出为 JSON 存到 data/backups/，并按保留份数清理。

应对场景：用户重新部署 / 宿主机故障后数据丢失。业务数据虽然在外部 MySQL，
但这里额外提供一份「离线快照」，多一层保险，且无需人工记得手动导出。
恢复：在网页「设置 → 整站备份 → 导入整站恢复」中上传对应 JSON 即可。
"""
import glob
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime

from app import database
from app.config import settings
from app.backup_crypto import encrypt_backup
from app.routers.backup import build_full_backup

BACKUP_DIR = os.path.join("data", "backups")
KEEP = 14  # 保留最近份数


def sqlite_snapshot(stamp: str) -> str | None:
    if database.engine is None or database.engine.dialect.name != "sqlite":
        return None
    os.makedirs(BACKUP_DIR, mode=0o700, exist_ok=True)
    path = os.path.join(BACKUP_DIR, f"sqlite-{stamp}.db")
    temporary = path + ".tmp"
    source = database.engine.raw_connection()
    try:
        with closing(sqlite3.connect(temporary)) as target:
            source.driver_connection.backup(target)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        source.close()
        if os.path.exists(temporary):
            os.remove(temporary)
    for old in sorted(glob.glob(os.path.join(BACKUP_DIR, "sqlite-*.db")))[:-7]:
        os.remove(old)
    return path


def _prune() -> None:
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "easysub-*.json")))
    for old in files[:-KEEP]:
        try:
            os.remove(old)
        except OSError:
            pass


def run_auto_backup() -> dict:
    """执行一次整站自动备份，返回 {ok, file, users} 或 {skipped}。"""
    if len(settings.backup_password) < 12:
        return {"skipped": "请配置至少 12 位的 BACKUP_PASSWORD，自动备份不会降级为明文"}
    if database.SessionLocal is None:
        return {"skipped": "数据库未配置"}
    os.makedirs(BACKUP_DIR, exist_ok=True)
    db = database.SessionLocal()
    try:
        payload = build_full_backup(db)
    finally:
        db.close()
    # 文件名带日期（同日覆盖，避免一天多份）
    stamp = datetime.utcnow().strftime("%Y%m%d")
    path = os.path.join(BACKUP_DIR, f"easysub-{stamp}.json")
    from tempfile import NamedTemporaryFile
    encrypted = encrypt_backup(payload, settings.backup_password)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=BACKUP_DIR, delete=False) as f:
            temporary = f.name
            json.dump(encrypted, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.remove(temporary)
    _prune()
    sqlite_snapshot(stamp)
    return {"ok": True, "file": os.path.basename(path), "users": len(payload["users"])}


def list_backups() -> list[dict]:
    """列出已有的自动备份文件（名称、大小、时间），供设置页展示。"""
    if not os.path.isdir(BACKUP_DIR):
        return []
    out = []
    for p in sorted(glob.glob(os.path.join(BACKUP_DIR, "easysub-*.json")), reverse=True):
        try:
            st = os.stat(p)
            out.append({
                "name": os.path.basename(p),
                "size": st.st_size,
                "modified": datetime.utcfromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            })
        except OSError:
            pass
    return out
