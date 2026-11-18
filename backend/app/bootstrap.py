"""数据库连接的引导配置：持久化到 data/db_config.json，并提供连接测试与 URL 构建。

说明：因为"数据库连接信息"本身就是要配置的对象，无法存进数据库，所以保存为
磁盘上的 JSON 文件（通过 Docker 卷持久化），类似 WordPress 的 wp-config。
"""
import json
import os
import ntpath
import sqlite3
from contextlib import closing
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

CONFIG_PATH = os.path.join("data", "db_config.json")


def config_exists() -> bool:
    return os.path.isfile(CONFIG_PATH)


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH) or ".", exist_ok=True)
    # 不保存多余字段
    if cfg.get("engine", "mysql") == "sqlite":
        sqlite_path(cfg.get("path", "data/easysub.db"))
    keep = {k: cfg[k] for k in ("engine", "path", "host", "port", "user", "password", "database") if k in cfg}
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(keep, f, ensure_ascii=False, indent=2)


def delete_config() -> None:
    if config_exists():
        os.remove(CONFIG_PATH)


def build_url(cfg: dict) -> str:
    if cfg.get("engine", "mysql") == "sqlite":
        path = sqlite_path(cfg.get("path", "data/easysub.db"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return URL.create("sqlite", database=path).render_as_string(hide_password=False)
    if cfg.get("engine", "mysql") != "mysql":
        raise ValueError("数据库类型必须为 sqlite 或 mysql")
    user = quote_plus(str(cfg["user"]))
    pw = quote_plus(str(cfg.get("password", "")))
    host = cfg["host"]
    port = int(cfg.get("port", 3306))
    database = cfg["database"]
    return f"mysql+pymysql://{user}:{pw}@{host}:{port}/{database}?charset=utf8mb4"


def sqlite_path(value: str) -> str:
    normalized = value.replace('\\', '/')
    if not normalized.startswith('data/') or '..' in normalized.split('/') or ntpath.isabs(value) or ntpath.splitdrive(value)[0]:
        raise ValueError("SQLite 路径必须位于 data/ 内，不能使用绝对路径或 ..")
    root = os.path.realpath('data')
    path = os.path.realpath(value)
    if os.path.commonpath([root, path]) != root or path == root:
        raise ValueError("SQLite 路径越界")
    return path


def auto_configure() -> None:
    if not config_exists() and os.environ.get("EASYSUB_DB") == "sqlite":
        save_config({"engine": "sqlite", "path": "data/easysub.db"})


def test_connection(cfg: dict) -> tuple[bool, str]:
    """尝试连接 MySQL，返回 (是否成功, 信息)。"""
    try:
        url = build_url(cfg)
    except (KeyError, ValueError, OSError) as e:
        return False, f"配置无效：{e}"
    if cfg.get("engine", "mysql") == "sqlite":
        try:
            path = sqlite_path(cfg.get("path", "data/easysub.db"))
            if not os.access(os.path.dirname(path), os.W_OK):
                return False, "SQLite 数据目录不可写"
            with closing(sqlite3.connect(path)) as conn:
                version = conn.execute('select sqlite_version()').fetchone()[0]
            return True, f"连接成功，SQLite 版本：{version}"
        except (OSError, sqlite3.Error) as e:
            return False, f"SQLite 连接失败：{e}"
    eng = create_engine(url, connect_args={"connect_timeout": 8})
    try:
        with eng.connect() as conn:
            version = conn.execute(text("SELECT VERSION()")).scalar()
        return True, f"连接成功，MySQL 版本：{version}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        eng.dispose()
