"""数据库引擎在运行时由网页安装向导配置后初始化（不再依赖启动时的环境变量）。"""
import time

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


# 运行时由 init_engine() 赋值；未配置前为 None
engine = None
SessionLocal = None

# 断线自愈：限制自动重连尝试频率，避免 MySQL 持续不可用时每个请求都阻塞重试
_last_reconnect_attempt = 0.0
_RECONNECT_INTERVAL = 15.0


def init_engine(url: str):
    """根据 SQLAlchemy URL 初始化全局引擎与会话工厂。"""
    global engine, SessionLocal
    connect_args = {}
    if url.startswith("mysql"):
        connect_args = {"connect_timeout": 10}
    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args=connect_args,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine


def is_configured() -> bool:
    return SessionLocal is not None


def connect_from_saved_config(force: bool = False) -> bool:
    """用磁盘上保存的连接配置初始化引擎并完成建表/迁移/种子/调度（幂等）。

    用于两个场景：
    1) 启动时 MySQL 尚未就绪（宿主机/容器一起重启，app 比 MySQL 先起来）——由启动重试调用；
    2) 运行期 MySQL 曾短暂不可用导致引擎未建立——由请求到达时自动调用，实现断线自愈，
       无需用户再走一遍安装向导重新填连接。
    成功返回 True。为避免持续故障时每个请求都阻塞重试，非 force 调用有最小间隔节流。
    """
    global _last_reconnect_attempt
    if SessionLocal is not None:
        return True

    now = time.monotonic()
    if not force and (now - _last_reconnect_attempt) < _RECONNECT_INTERVAL:
        return False
    _last_reconnect_attempt = now

    # 延迟导入避免与这些模块产生循环依赖
    from app import bootstrap, migrate
    from app.seed import seed_all
    from app.services import scheduler

    if not bootstrap.config_exists():
        return False
    try:
        init_engine(bootstrap.build_url(bootstrap.load_config()))
        Base.metadata.create_all(bind=engine)
        migrate.run_migrations(engine)
        db = SessionLocal()
        try:
            seed_all(db)
        finally:
            db.close()
        scheduler.start_scheduler()  # 幂等，已启动则跳过
        return True
    except Exception:  # noqa: BLE001
        reset_engine()
        return False


def reset_engine():
    global engine, SessionLocal
    if engine is not None:
        engine.dispose()
    engine = None
    SessionLocal = None


def get_db():
    if SessionLocal is None:
        # 断线/启动竞态自愈：若磁盘已有配置，尝试用它自动重连，避免要求用户重走安装向导
        if not connect_from_saved_config():
            raise HTTPException(
                status_code=503,
                detail="数据库尚未配置或暂时不可用，请稍后重试；若为首次安装请在安装向导中配置",
            )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
