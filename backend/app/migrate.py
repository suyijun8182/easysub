"""轻量级在线迁移：为已存在的表补齐新增列。

SQLAlchemy 的 create_all 只会创建缺失的「表」，不会给已存在的表加「列」。
对接用户已有 MySQL 的场景，这里在启动/初始化时检查并按需 ALTER TABLE。
MySQL 8 不支持 ADD COLUMN IF NOT EXISTS，因此先查 information_schema 再决定。
"""
from sqlalchemy import text
from sqlalchemy.engine import Engine

# (表名, 列名, 列定义) —— 仅追加，不删除/改名，确保安全幂等
_COLUMNS = [
    ("subscriptions", "sort", "INT NOT NULL DEFAULT 0"),
    ("subscriptions", "last_renewed_at", "DATE NULL"),
    ("subscriptions", "remark", "VARCHAR(255) NULL"),
    ("subscriptions", "ipv4", "VARCHAR(64) NULL"),
    ("subscriptions", "ipv6", "VARCHAR(64) NULL"),
    ("users", "category_order", "JSON NULL"),
    ("users", "email_verified", "TINYINT(1) NOT NULL DEFAULT 1"),
    ("users", "is_approved", "TINYINT(1) NOT NULL DEFAULT 1"),
    ("users", "email_code", "VARCHAR(16) NULL"),
    ("users", "email_code_expires", "DATETIME NULL"),
    ("users", "telegram_admin_id", "VARCHAR(64) NULL"),
    ("users", "telegram_api_base", "VARCHAR(255) NULL"),
    ("users", "telegram_proxy", "VARCHAR(255) NULL"),
    ("users", "notify_config", "JSON NULL"),
    ("users", "calendar_token", "VARCHAR(64) NULL"),
    ("users", "monthly_budget", "DOUBLE NULL"),
    ("users", "notify_settings", "JSON NULL"),
    ("subscriptions", "trial_end", "DATE NULL"),
    ("subscriptions", "cancel_by", "DATE NULL"),
    ("subscriptions", "card_last4", "VARCHAR(8) NULL"),
    ("subscriptions", "card_expiry", "VARCHAR(8) NULL"),
    ("users", "totp_secret", "VARCHAR(64) NULL"),
    ("users", "totp_enabled", "TINYINT(1) NOT NULL DEFAULT 0"),
]


def _column_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).scalar()
    return bool(row)


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = :t"
        ),
        {"t": table},
    ).scalar()
    return bool(row)


def run_migrations(engine: Engine) -> None:
    """对 MySQL 执行幂等的列补齐。非 MySQL（如测试用 sqlite）直接跳过。"""
    if engine is None or not engine.url.get_backend_name().startswith("mysql"):
        return
    with engine.begin() as conn:
        for table, column, ddl in _COLUMNS:
            try:
                if not _table_exists(conn, table):
                    continue
                if _column_exists(conn, table, column):
                    continue
                conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {ddl}"))
                print(f"[migrate] 已为 {table} 添加列 {column}")
            except Exception as e:  # noqa: BLE001
                print(f"[migrate] 跳过 {table}.{column}：{e}")
