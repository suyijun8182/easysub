# v1.14.1 更新与回滚

本版修复 Android 首次连接后令牌对象导致同步中断的问题。相比 v1.14.0 没有数据库结构变更。

## 更新服务器

先保留现有 Compose 配置、`.env`、MySQL、`/app/data` 和 `JWT_SECRET`。在原 Compose 项目中把 app 服务镜像改为：

```yaml
image: suyijun8182/easysub:v1.14.1
```

然后按原文件名和服务名执行：

```bash
docker compose -f docker-compose.hub.yml pull app
docker compose -f docker-compose.hub.yml up -d --no-deps app
docker compose -f docker-compose.hub.yml logs --tail=100 app
```

也可用 `ghcr.io/suyijun8182/easysub:v1.14.1`。两个仓库都提供 `linux/amd64` 和 `linux/arm64`。`latest` 同步指向本版。

打开 `/api/health`，检查 `version` 为 `1.14.1`、`configured` 为 `true`、`sync_protocol` 为 `1`。本版不需要数据库迁移。

## 更新 Android Alpha

从 [GitHub Release](https://github.com/suyijun8182/easysub/releases/tag/v1.14.1) 下载 `EasySub-0.1.1-alpha-debug.apk` 和 `SHA256SUMS`。可覆盖安装同签名的 0.1.0 Alpha；不要卸载 App，以保留 Keystore 加密的本地资料。

首次连接时核对服务器、账号及本地/网页订阅数，再选择“确认保存并开始同步”。连接后应立即开始合并，无需重启。请先保留一份 App 内加密备份。

## 回滚

服务器回滚：把原 app 镜像改回 `suyijun8182/easysub:v1.14.0`，按原 Compose 项目重建。保留 MySQL、数据卷与 `JWT_SECRET`。v1.14.1 没有数据库迁移。

App 回滚：安装 v1.14.0 Release 中的 `EasySub-0.1.0-alpha-debug.apk`，不要卸载或清除应用数据。

完整的数据保留、容器更新和回滚背景见 [v1.14.0 更新方案](update-v1.14.0.md)。
