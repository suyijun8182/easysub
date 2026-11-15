#!/usr/bin/env bash
# 省心订阅 EasySub —— 增量升级脚本（不会清空数据）
#
# 用法：在项目目录执行  ./update.sh
# 作用：拉取最新代码 → 仅重建 app 镜像（复用未变更的层）→ 重启 app 容器 → 检查应用和数据库
# 数据安全：你的订阅数据在【外部 MySQL】，连接配置与图标在命名卷 app_data 中，
#          本脚本不使用 `down -v`，不会触碰这些数据。
set -e

cd "$(dirname "$0")"

echo "==> 1/4 拉取最新代码 (git pull)"
if [ -d .git ]; then
  git pull --ff-only
else
  echo "    跳过：当前目录不是 git 仓库（请手动覆盖最新代码后再运行）"
fi

echo "==> 2/4 重建并启动 app（自动复用缓存层，依赖未变则很快）"
docker compose up -d --build app

echo "==> 3/4 等待健康检查"
healthy=false
for attempt in {1..30}; do
  if docker compose exec -T app python -c '
import json, urllib.request
from app import bootstrap
h = json.load(urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=5))
assert h["status"] == "ok"
if bootstrap.config_exists():
    status = json.load(urllib.request.urlopen("http://127.0.0.1:8000/api/setup/status", timeout=20))
    assert status["configured"], "database not ready"
    from sqlalchemy import create_engine, text
    engine = create_engine(bootstrap.build_url(bootstrap.load_config()), connect_args={"connect_timeout": 5})
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    finally:
        engine.dispose()
' ; then
    healthy=true
    break
  fi
  sleep 2
done
if [ "$healthy" != true ]; then
  echo "升级后的应用或数据库尚未就绪，请检查日志；未清理旧镜像。" >&2
  docker compose logs --tail=50 app
  exit 1
fi
docker compose ps

echo "==> 4/4 已保留旧镜像，供需要时回滚"

echo "✅ 升级完成。数据与数据库连接均已保留。"
echo "   查看日志： docker compose logs -f app"
