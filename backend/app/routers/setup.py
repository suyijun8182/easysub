from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import bootstrap, database, migrate
from app.seed import seed_all
from app.services import scheduler

router = APIRouter(prefix="/api/setup", tags=["setup"])


class DBConfig(BaseModel):
    host: str
    port: int = 3306
    user: str
    password: str = ""
    database: str


def _initialize(cfg: dict) -> None:
    """连接成功后：建引擎 → 建表 → 写入预置数据 → 启动定时任务。"""
    database.init_engine(bootstrap.build_url(cfg))
    database.Base.metadata.create_all(bind=database.engine)
    migrate.run_migrations(database.engine)
    db = database.SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
    scheduler.start_scheduler()


@router.get("/status")
def status():
    # 若磁盘已有配置但引擎未就绪（如启动时 MySQL 未准备好），尝试自愈重连，
    # 这样前端刷新即可恢复，而不会误判为「未配置」再次弹出安装向导。
    if not database.is_configured() and bootstrap.config_exists():
        database.connect_from_saved_config()
    return {
        "configured": database.is_configured(),  # 引擎已就绪可用
        "config_present": bootstrap.config_exists(),  # 磁盘上已有配置文件
    }


@router.post("/test")
def test(cfg: DBConfig):
    ok, msg = bootstrap.test_connection(cfg.model_dump())
    if not ok:
        raise HTTPException(400, f"连接失败：{msg}")
    return {"ok": True, "message": msg}


@router.post("/save")
def save(cfg: DBConfig):
    if database.is_configured():
        raise HTTPException(400, "系统已完成数据库配置")
    ok, msg = bootstrap.test_connection(cfg.model_dump())
    if not ok:
        raise HTTPException(400, f"连接失败：{msg}")
    try:
        _initialize(cfg.model_dump())
    except Exception as e:  # noqa: BLE001
        database.reset_engine()
        raise HTTPException(500, f"初始化失败：{type(e).__name__}: {e}")
    bootstrap.save_config(cfg.model_dump())
    return {"ok": True, "message": "数据库已配置并初始化完成，请登录"}
