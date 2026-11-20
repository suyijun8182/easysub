# EasySub · 省心订阅

Self-hosted subscription / renewal manager with **14 notification channels**, so you never let a subscription — or a SIM keep-alive plan — expire.

自托管的订阅 / 续费 / 保号管理系统，通过 **14 种通知渠道**（Telegram、飞书、QQ、Bark、Email、Pushplus、Server酱、企业微信、钉钉、Discord、Slack、ntfy、Gotify、Webhook）提醒续费，避免因忘记而过期。

- **Source / 源码**: https://github.com/suyijun8182/easysub
- **Tags**: `latest`, `vX.Y.Z` per release — multi-arch `linux/amd64` + `linux/arm64`
- **GHCR mirror / 国内镜像**: `ghcr.io/suyijun8182/easysub:latest`
- **Changelog / 更新日志**: https://github.com/suyijun8182/easysub/blob/main/CHANGELOG.md
- **Live demo / 在线体验**: https://easysub.vviip.dpdns.org:8443/ （`guest` / `guest123`）

## 🆕 v2.1.0

- **SQLite is now the default — no MySQL needed.** Existing MySQL deployments keep working with no changes.
  **支持 SQLite 并设为默认**，不用再准备 MySQL；原来的 MySQL 部署升级后照常运行。
- **Month-end renewals no longer drift** (Jan 31 → Feb 28 → Mar 31), and the renewal preview no longer shows a day early in time zones west of UTC. Dates that already drifted to the 28th need one manual fix.
  **修复月末续费漂移**和时区导致的预览少一天。已经漂移到 28 号的订阅需要手动改回一次。
- **One-command Linux install without Docker** — see the GitHub README.
  **新增不依赖 Docker 的 Linux 一键安装**，详见 GitHub README。
- **Android 0.3.1-alpha** (APK on GitHub Releases): the phone now fetches exchange rates online by itself, so they no longer show as unavailable.
  **Android 0.3.1-alpha**：手机端汇率改为直接联网获取，不再显示「未缓存」。

## Quick start / 快速开始（SQLite，推荐）

```bash
docker run -d --name easysub \
  -p 8842:8000 \
  -e EASYSUB_DB=sqlite \
  -e TZ=Asia/Shanghai \
  -v easysub_data:/app/data \
  --restart unless-stopped \
  suyijun8182/easysub:latest
```

Open `http://<host>:8842` and register — the first account becomes the administrator. With `EASYSUB_DB=sqlite` the database is created on first start and the setup wizard is skipped. **Keep the `easysub_data` volume**: it holds the database, the auto-generated JWT key, icons and backups.

打开 `http://<服务器IP>:8842` 注册，第一个账号就是管理员。设置 `EASYSUB_DB=sqlite` 后首次启动会自动建库，跳过安装向导。**一定要保留 `easysub_data` 数据卷**，数据库、自动生成的密钥、图标和备份都在里面。

### docker-compose (SQLite)

```yaml
services:
  app:
    image: suyijun8182/easysub:latest
    container_name: easysub
    restart: unless-stopped
    environment:
      EASYSUB_DB: sqlite
      TZ: Asia/Shanghai
      # BACKUP_PASSWORD: at-least-12-characters   # enables daily encrypted backups
    volumes:
      - easysub_data:/app/data
    ports:
      - "8842:8000"
volumes:
  easysub_data:
```

### Using your own MySQL 8 / 使用已有的 MySQL 8

Leave out `EASYSUB_DB`. On first visit the setup wizard opens: choose **MySQL**, enter the connection details, test, then save. Inside a container, use the MySQL host's real IP or service name, not `localhost`.

不设置 `EASYSUB_DB`，首次访问会进入安装向导：选择 **MySQL**，填写连接信息，测试后保存。容器里不能填 `localhost`，要填实际 IP 或服务名。

## Environment variables / 环境变量

All optional. 全部可选。

| Var | Description / 说明 |
|-----|-------------|
| `EASYSUB_DB` | `sqlite` = create a SQLite database on first start and skip the wizard. Ignored once a database is configured. 首次启动自动初始化 SQLite。 |
| `JWT_SECRET` | Strong custom key. If empty, a persistent key is generated in `/app/data/jwt_secret`. 留空时自动生成并保存在数据卷。 |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` | Pre-created admin. Without `ADMIN_PASSWORD`, the first registered account becomes admin. 不设密码时，第一个注册的账号是管理员。 |
| `BACKUP_PASSWORD` | 12+ characters; enables daily encrypted backups (SQLite also keeps 7 database snapshots). 每日自动加密备份的密码。 |
| `TZ` | Time zone, e.g. `Asia/Shanghai`. 时区。 |
| `REMINDER_SCAN_TIME` | Daily reminder time, default `09:00`. 每日提醒时间。 |
| `REQUIRE_ADMIN_APPROVAL` | Require admin approval for sign-ups, default `false`. 注册是否需要审核。 |
| `OUTBOUND_PRIVATE_ALLOWLIST` | LAN targets notifications may reach, e.g. `nas.lan:5000,192.168.1.10:7890`. 允许访问的内网地址。 |
| `TELEGRAM_BOT_TOKEN` | Optional; can also be set in the web UI. 可在网页中设置。 |
| `EXCHANGE_API_BASE` / `EXCHANGE_API_URL` | Exchange-rate source (defaults provided). 汇率数据源。 |

## Volume / 数据卷

- `/app/data` — SQLite database, DB connection config, JWT key, uploaded icons and backups. **Persist this.**
  SQLite 数据库、连接配置、JWT 密钥、图标和备份都在这里，**必须持久化**。

## Upgrade / 升级

Upgrading only swaps the image; new columns are migrated automatically on start.
升级只更换镜像，新增字段在启动时自动迁移，数据不会丢失。

```bash
# compose
docker compose pull && docker compose up -d

# docker run: pull, then recreate with the same volume and environment
docker pull suyijun8182/easysub:latest
docker rm -f easysub && docker run -d --name easysub ... suyijun8182/easysub:latest
```

NAS GUI: re-pull the `latest` tag and recreate the container, keeping the `/app/data` mapping and environment unchanged.
NAS 图形界面：重新拉取 `latest`，再重建容器，`/app/data` 映射和环境变量保持不变。

> **Back up first / 升级前先备份**: Settings → Data backup → export JSON (admins: full-site backup).
> 在“设置 → 数据备份”导出 JSON，管理员可导出整站备份。

### MySQL → SQLite

Export a **full-site backup** from the old instance, start a new SQLite instance **on a new volume**, register the admin, import the backup in Settings → Data backup, check the data, then switch over. Copy `data/icons` separately if you uploaded custom icons.

在旧实例导出**整站备份** → 用**新的数据卷**启动 SQLite 实例并注册管理员 → 在“设置 → 数据备份”导入 → 核对数据后切换入口。上传过的自定义图标需要单独复制 `data/icons`。

## Features / 功能

Multi-user with open sign-up · recurring & one-time subscriptions with bulk actions and drag reordering · carrier keep-alive mode · **14 notification channels** with quiet hours & weekly digest · trial / cancel-by / card-expiry reminders · monthly budget · built-in library of hundreds of services (icons ship with the image) · dashboard, reports & CSV export · calendar + `.ics` feed · multi-currency with live FX · personal & full-site backup/restore + daily encrypted auto-backup · 2FA · API tokens · encrypted secrets · auto DB reconnect & auto-migration · PWA · Android app with two-way sync (alpha) · Home Assistant endpoint · 中文 / English / Русский · 6 themes.

## NAS install guides / NAS 安装教程

Synology / QNAP / fnOS / Unraid / TrueNAS — see [各厂家NAS安装教程.md](https://github.com/suyijun8182/easysub/blob/main/%E5%90%84%E5%8E%82%E5%AE%B6NAS%E5%AE%89%E8%A3%85%E6%95%99%E7%A8%8B.md).

## License

MIT · Author TG [@Aiden_SU](https://t.me/Aiden_SU) · aidensu8182@gmail.com
