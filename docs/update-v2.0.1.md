# 升级到 v2.0.1

本版修复未登录静态文件读取、公开的 JWT 示例密钥、默认管理员凭据、安装接口探测、SVG 脚本执行、已知依赖漏洞、登录锁定和 API Token 明文存储问题。
保留已有 MySQL、账号、订阅和数据卷，不修改 Android 版本号。

## 升级前

1. 导出个人及整站备份，并保存 MySQL 快照、原 Compose/.env、原 `JWT_SECRET` 和 `/app/data` 数据卷副本。整站导出不能替代回滚用的完整数据库快照。
2. 检查原 `JWT_SECRET`。强自定义密钥继续使用原值；未设置、为空或使用文档示例值时，本版会自动生成随机密钥，保存到 `data/jwt_secret`（容器内 `/app/data/jwt_secret`）。必须保留数据卷，不要把该文件提交或公开。
3. 原来使用默认或示例 JWT 密钥的会话将在升级后失效，所有设备需要重新登录。强自定义密钥保持不变时，升级本身不会使既有会话失效。App 本地资料与待同步修改继续保留。
4. 不再预置 `admin/admin123`。新装且未配置有效 `ADMIN_PASSWORD` 时，第一个注册的账号成为管理员；显式设置 `admin123` 也不会创建初始管理员。已有管理员保留，仍使用默认密码时，请立即从警告横幅进入设置修改。
5. API Token 只在创建时显示一次。已有脚本继续使用原明文 Token，服务器自动将存量 Token 改为 SHA-256 哈希；无法再从数据库找回原值，遗失时请创建新 Token。

首次启动后请尽快完成安装向导，不要把未完成安装的实例暴露到公网。
`BACKUP_PASSWORD`、`OUTBOUND_PRIVATE_ALLOWLIST` 沿用 v2.0.0 的配置方式，自动备份密码与 JWT 密钥分别保存。

## Docker

发布后，将现有 app 服务镜像固定为 `suyijun8182/easysub:v2.0.1`，或 `ghcr.io/suyijun8182/easysub:v2.0.1`。
在原 Compose 项目中运行：

```bash
docker compose pull app
docker compose up -d app
docker compose logs --tail=100 app
```

使用仓库的 Hub Compose 文件时，在每条命令中加入 `-f docker-compose.hub.yml`。
`docker run` 或 NAS 部署保留原端口、网络、环境变量与 `/app/data` 挂载，只替换 app 镜像并重建容器。
保留强自定义 `JWT_SECRET`，不要在重建时重新生成；使用自动密钥的实例不要删除 `jwt_secret` 或执行 `down -v`。

启动会幂等迁移以已知示例密钥加密的通知字段和同步记录、变更、回执，改用当前密钥加密；无法解密的密文会原样保留，不会替换成空值。
自定义密钥丢失的历史密文无法通过示例密钥恢复，需找回原密钥或重新填写相关配置。

## 备份和账号

整站备份继续使用至少 12 位的独立密码加密，恢复时填写同一密码。MySQL 快照应与数据卷和环境配置配套保存。
更换密码后旧会话会撤销。API Token 是独立凭据，本次升级保留已有 Token 的可用性；发现泄漏时请在设置中吊销并重新创建。
不再预置管理员不会删除已有账号，也不会把后续注册用户提升为管理员。

## Android Alpha

Android 保持 0.1.3 Alpha，本次不发布新的 APK，不修改 `frontend/android/`。
因示例密钥替换而失效的 App 会话需要重新登录，离线资料和待同步修改应继续保留。

## 验证与回滚

升级后检查：

- `/api/health` 返回 `version: 2.0.1`、`configured: true`、`sync_protocol: 1`。未配置数据库的实例只能证明进程可访问。
- 未设置 JWT 密钥时，`/app/data/jwt_secret` 已生成；登录后重启容器，会话仍然有效，说明挂载保留了密钥。
- `curl --path-as-is "http://127.0.0.1:8842/%2e%2e/data/db_config.json"` 返回前端页面，不包含数据库配置；正常前端路由仍可打开。
- 登录及两步验证、默认密码警告与修改密码、通知渠道测试、App 双向同步、备份导出和隔离恢复正常。
- 上传的 SVG 仍能作为图标显示，直接访问时响应含 `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox` 和 `X-Content-Type-Options: nosniff`。
- 已配置系统的 `POST /api/setup/test` 返回 400；已有 API Token 仍可认证，新 Token 仅显示一次，列表不显示 Token。

需要回滚时：

1. 停止 app，保存当前 MySQL、数据卷与配置的副本，以便排查及恢复升级后的新增资料。
2. 恢复升级前配套保存的 MySQL 快照、`/app/data` 副本和环境配置（包括原 `JWT_SECRET`）。通知和同步密文、API Token 已迁移，不能只换回旧镜像：v2.0.0 不能用哈希值认证原 API Token，也不会读取自动生成的密钥文件。
3. 将镜像固定为 `suyijun8182/easysub:v2.0.0` 或对应 GHCR 镜像，按原部署方式重新创建 app 容器。检查登录、通知、同步和旧 Token。

回滚恢复快照会丢弃快照之后的数据库变更，应事先保留当前副本。旧版仍包含本次修复的安全问题，回滚仅用于隔离环境中的故障恢复。

依赖选型依据：[FastAPI 0.133.0 PyPI 元数据](https://pypi.org/pypi/fastapi/0.133.0/json) 允许 `starlette>=0.40.0`，而 [0.132.1](https://pypi.org/pypi/fastapi/0.132.1/json) 仍限制 `<1.0.0`；本版选择可覆盖审计最高修复版本 1.3.1 的最小 FastAPI 版本，不单独钉 Starlette。
