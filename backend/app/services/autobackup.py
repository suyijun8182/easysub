"""定时自动备份：每天把整站数据导出为 JSON 存到 data/backups/，并按保留份数清理。

应对场景：用户重新部署 / 宿主机故障后数据丢失。业务数据虽然在外部 MySQL，
但这里额外提供一份「离线快照」，多一层保险，且无需人工记得手动导出。
恢复：在网页「设置 → 整站备份 → 导入整站恢复」中上传对应 JSON 即可。
"""
import glob
import json
import os
from datetime import datetime

from app import database
from app.routers.backup import build_full_backup

BACKUP_DIR = os.path.join("data", "backups")
KEEP = 14  # 保留最近份数


def _prune() -> None:
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "easysub-*.json")))
    for old in files[:-KEEP]:
        try:
            os.remove(old)
        except OSError:
            pass


def run_auto_backup() -> dict:
    """执行一次整站自动备份，返回 {ok, file, users} 或 {skipped}。"""
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    _prune()
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
