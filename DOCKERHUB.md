# EasySub · 省心订阅

v2.0.2：修复中国大陆添加订阅时服务图标加载慢、页面卡顿的问题（[#2](https://github.com/suyijun8182/easysub/issues/2)）。镜像自带的服务图标直接从本地读取，下载不到时显示首字母占位图；直接更新镜像即可，无需改配置。Android 0.2.0 Alpha 客户端同步更新，详见 [Android 0.2.0 说明](https://github.com/suyijun8182/easysub/blob/main/docs/android-0.2.0.md)。

v2.0.1 安全公告：修复匿名文件读取、公开 JWT 示例密钥、默认管理员凭据、安装接口探测、SVG 脚本执行、依赖漏洞、跨 IP 登录锁定及 API Token 明文存储。请阅读 [升级与回滚说明](https://github.com/suyijun8182/easysub/blob/main/docs/update-v2.0.1.md)。原来使用示例 JWT 密钥的设备需重新登录；自动密钥保存在 `data/jwt_secret`，必须保留数据卷。API Token 只在创建时显示一次。自动备份和内网出站配置沿用 v2.0.0。

Self-hosted subscription / renewal manager with **14 notification channels** so you never let a subscription — or a SIM keep-alive plan — expire.

自托管的订阅 / 续费 / 保号管理系统，**14 种通知渠道**（Telegram / 飞书 / QQ / Bark / Email / Pushplus / Server酱 / 企业微信 / 钉钉 / Discord / Slack / ntfy / Gotify / Webhook）提醒续费，防止忘记导致过期。

- **Source / 源码**: https://github.com/suyijun8182/easysub
- **Tags**: `latest`, `v*` (per release) — multi-arch `linux/amd64` + `linux/arm64`
- **GHCR mirror**: `ghcr.io/suyijun8182/easysub:latest`
- **Changelog / 更新日志**: https://github.com/suyijun8182/easysub/blob/main/CHANGELOG.md

> The image does **not** bundle a database. On first visit a web wizard asks for **your existing MySQL 8** connection.
> 镜像**不内置数据库**，首次访问网页向导填入你已有的 MySQL 连接即可。

## Quick start / 快速开始

```bash
docker run -d --name easysub \
  -p 8842:8000 \
  -e ADMIN_USERNAME=admin \
  -e TZ=Asia/Shanghai \
  -v easysub_data:/app/data \
  --restart unless-stopped \
  suyijun8182/easysub:latest
```

Then open `http://<host>:8842`, finish the DB wizard, register the first administrator account, and log in. Complete setup promptly; keep unconfigured instances off the public Internet.

首次启动后请尽快完成安装向导，不要把未完成安装的实例暴露到公网。

不再预置 `admin/admin123`。不设置 `ADMIN_PASSWORD` 时，第一个注册的账号就是管理员。如需预置账号，可取消注释示例 `# ADMIN_PASSWORD=your-strong-password` 并填写自己的强密码。

## docker-compose

```yaml
services:
  app:
    image: suyijun8182/easysub:latest
    container_name: easysub
    restart: unless-stopped
    environment:
      JWT_SECRET: ""  # Auto-generated in /app/data/jwt_secret; persist the volume
      TZ: Asia/Shanghai
      ADMIN_USERNAME: admin
      # ADMIN_PASSWORD: your-strong-password
      ADMIN_EMAIL: admin@example.com
    volumes:
      - easysub_data:/app/data
    ports:
      - "8842:8000"
volumes:
  easysub_data:
```

## Environment variables / 环境变量

| Var | Description |
|-----|-------------|
| `JWT_SECRET` | Optional strong custom key. Empty or example values generate a persistent key in `/app/data/jwt_secret`; keep the volume. |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` | Optional initial admin. Without ADMIN_PASSWORD, the first registered account becomes admin. |
| `TZ` | Timezone, e.g. `Asia/Shanghai`. |
| `REMINDER_SCAN_TIME` | Daily scan time for reminders, e.g. `09:00`. |
| `REQUIRE_ADMIN_APPROVAL` | Require admin approval for new sign-ups. Default `false` (sign up and log in right away). |
| `TELEGRAM_BOT_TOKEN` | Optional; can also be set in the web UI. |
| `EXCHANGE_API_BASE` / `EXCHANGE_API_URL` | Exchange-rate source (defaults provided). |

## Volumes

- `/app/data` — signing key (`jwt_secret`), DB connection config (`db_config.json`), uploaded icons and backups. Persist this.

## Upgrade / 升级

**v2.0.1 安全更新**：发布后可固定镜像 `suyijun8182/easysub:v2.0.1` 或对应 GHCR 镜像。升级前保存 MySQL 快照、原 Compose/.env 和 `/app/data` 副本；保留强自定义 `JWT_SECRET`。自动密钥写入数据卷，旧示例密文和 API Token 启动时幂等迁移。

保持原项目、端口、反向代理和数据卷；只更新 app 镜像并重建。`/api/health` 应显示 `version: 2.0.1`、`configured: true`、`sync_protocol: 1`。回滚需配套恢复升级前的数据库、数据卷和配置，不能只换旧镜像。完整步骤：[v2.0.1 更新说明](https://github.com/suyijun8182/easysub/blob/main/docs/update-v2.0.1.md)。

Data lives in **your MySQL**; upgrading only swaps the image and is non-destructive.
数据都在**你自己的 MySQL** 里，升级只换镜像，不会动数据。

```bash
# compose
docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d

# docker run
docker pull suyijun8182/easysub:latest
# 使用原来的环境、网络、端口和挂载配置重建，镜像改为固定版本。
# 保留强自定义 JWT_SECRET 和 /app/data（包含自动密钥 jwt_secret），不要重新生成或删除密钥。
```

NAS 图形界面：重新拉取 `latest` 标签 → 重建容器，保持 `/app/data` 映射与环境变量不变。
新增列由程序启动时**自动迁移**（幂等，不丢旧数据）。

> **升级前建议先备份**：网页 **设置 → 数据备份** 导出 JSON；管理员可用 **整站备份** 导出全部成员数据。
> Before upgrading, export a backup from **Settings → Data backup** (admins: full-site backup).

## What's new / 最近更新

- **v2.0.1** — Security fixes for file traversal, signing secrets, default admin credentials, setup probes, SVG scripts, dependencies, login throttling and hashed API tokens. No default admin/admin123; the first registered account becomes admin when ADMIN_PASSWORD is unset.

- **v1.13.0** — Bulk actions on subscriptions (renew / enable / disable / move / delete) and a button-based reorder mode; fixed login errors and the 2FA prompt vanishing on a fresh browser; keyboard & screen-reader fixes across forms and dialogs. 订阅批量操作与按钮排序；修复登录报错不显示、新浏览器下两步验证无法登录；表单与弹窗无障碍改进。
- **v1.12.1** — Sign-up no longer needs admin approval; set `REQUIRE_ADMIN_APPROVAL=true` to keep it. 注册后直接可用，如需审核设 `REQUIRE_ADMIN_APPROVAL=true`。
- **v1.12.0** — Full UI redesign: remaining-cycle bar on every card, green / yellow / red expiry states, renewal-timeline dashboard, mobile bottom tab bar. Backup import now shows the real error instead of "invalid file format". 全站 UI 改版；导入备份报错显示真实原因。
- **v1.11.x** — WeCom self-built app push; fixes for the notification panel disappearing and for deleting subscriptions that had sent reminders. 企业微信自建应用推送；修复通知面板消失与删除订阅报错。

## Features

Multi-user (JWT, admin/user roles, open sign-up — admin approval optional) · redesigned UI (remaining-cycle bar, renewal timeline, mobile tab bar) · recurring & one-time subscriptions with **bulk actions** and button / drag reordering · keyboard & screen-reader friendly · **14 notification channels** (Telegram / Feishu / QQ / Bark / Email / Pushplus / ServerChan / **WeCom — group robot *or* self-built app** / DingTalk / Discord / Slack / ntfy / Gotify / Webhook) with quiet hours & weekly digest · trial / cancel / card-expiry reminders · monthly budget with overspend alert · built-in service library (100s of presets incl. dozens of carriers & eSIM) · multi-language (中/EN/RU) · 6 themes (incl. system-follow) · multi-currency with live FX · dashboard & reports + **CSV export** · Apple-style calendar + **.ics feed** · per-user & **admin full-site** backup/restore + **daily auto-backup** + CSV import/export · **2FA · API tokens · encrypted secrets** · **auto DB reconnect** & auto-migration · **PWA installable** · **in-app update check** · Home Assistant integration.

## NAS install guides

Synology / QNAP / fnOS / Unraid / TrueNAS — see [各厂家NAS安装教程.md](https://github.com/suyijun8182/easysub/blob/main/%E5%90%84%E5%8E%82%E5%AE%B6NAS%E5%AE%89%E8%A3%85%E6%95%99%E7%A8%8B.md) in the repo.

## License

MIT · Author TG [@Aiden_SU](https://t.me/Aiden_SU) · aidensu8182@gmail.com
