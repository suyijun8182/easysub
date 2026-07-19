# EasySub · 省心订阅

Self-hosted subscription / renewal manager with **14 notification channels** so you never let a subscription — or a SIM keep-alive plan — expire.

自托管的订阅 / 续费 / 保号管理系统，**14 种通知渠道**（Telegram / 飞书 / QQ / Bark / Email / Pushplus / Server酱 / 企业微信 / 钉钉 / Discord / Slack / ntfy / Gotify / Webhook）提醒续费，防止忘记导致过期。

- **Source / 源码**: https://github.com/suyijun8182/easysub
- **Tags**: `latest`, `v*` (per release) — multi-arch `linux/amd64` + `linux/arm64`
- **GHCR mirror**: `ghcr.io/suyijun8182/easysub:latest`

> The image does **not** bundle a database. On first visit a web wizard asks for **your existing MySQL 8** connection.
> 镜像**不内置数据库**，首次访问网页向导填入你已有的 MySQL 连接即可。

## Quick start / 快速开始

```bash
docker run -d --name easysub \
  -p 8842:8000 \
  -e JWT_SECRET="$(openssl rand -hex 32)" \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=admin123 \
  -e TZ=Asia/Shanghai \
  -v easysub_data:/app/data \
  --restart unless-stopped \
  suyijun8182/easysub:latest
```

Then open `http://<host>:8842`, finish the DB wizard, and log in.

## docker-compose

```yaml
services:
  app:
    image: suyijun8182/easysub:latest
    container_name: easysub
    restart: unless-stopped
    environment:
      JWT_SECRET: change-me-to-a-random-secret
      TZ: Asia/Shanghai
      ADMIN_USERNAME: admin
      ADMIN_PASSWORD: admin123
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
| `JWT_SECRET` | **Required.** Random secret for auth tokens. |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` | Initial admin account created on first init. |
| `TZ` | Timezone, e.g. `Asia/Shanghai`. |
| `REMINDER_SCAN_TIME` | Daily scan time for reminders, e.g. `09:00`. |
| `TELEGRAM_BOT_TOKEN` | Optional; can also be set in the web UI. |
| `EXCHANGE_API_BASE` / `EXCHANGE_API_URL` | Exchange-rate source (defaults provided). |

## Volumes

- `/app/data` — DB connection config (`db_config.json`) + uploaded icons. Persist this.

## Upgrade / 升级

Data lives in **your MySQL**; upgrading only swaps the image and is non-destructive.
数据都在**你自己的 MySQL** 里，升级只换镜像，不会动数据。

```bash
# compose
docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d

# docker run
docker pull suyijun8182/easysub:latest
docker rm -f easysub && docker run -d --name easysub ... suyijun8182/easysub:latest   # 保持 -v easysub_data:/app/data 不变
```

NAS 图形界面：重新拉取 `latest` 标签 → 重建容器，保持 `/app/data` 映射与环境变量不变。
新增列由程序启动时**自动迁移**（幂等，不丢旧数据）。

> **升级前建议先备份**：网页 **设置 → 数据备份** 导出 JSON；管理员可用 **整站备份** 导出全部成员数据。
> Before upgrading, export a backup from **Settings → Data backup** (admins: full-site backup).

## Features

Multi-user (JWT, admin/user roles) · recurring & one-time subscriptions · **14 notification channels** (Telegram / Feishu / QQ / Bark / Email / Pushplus / ServerChan / WeCom / DingTalk / Discord / Slack / ntfy / Gotify / Webhook) with quiet hours & weekly digest · trial / cancel / card-expiry reminders · monthly budget with overspend alert · built-in service library (100s of presets incl. dozens of carriers & eSIM) · multi-language (中/EN/RU) · 6 themes (incl. system-follow) · multi-currency with live FX · dashboard & reports + **CSV export** · Apple-style calendar + **.ics feed** · per-user & **admin full-site** backup/restore + **daily auto-backup** + CSV import/export · **2FA · API tokens · encrypted secrets** · **auto DB reconnect** & auto-migration · **PWA installable** · **in-app update check** · Home Assistant integration.

## NAS install guides

Synology / QNAP / fnOS / Unraid / TrueNAS — see [各厂家NAS安装教程.md](https://github.com/suyijun8182/easysub/blob/main/%E5%90%84%E5%8E%82%E5%AE%B6NAS%E5%AE%89%E8%A3%85%E6%95%99%E7%A8%8B.md) in the repo.

## License

MIT · Author TG [@Aiden_SU](https://t.me/Aiden_SU) · aidensu8182@gmail.com
