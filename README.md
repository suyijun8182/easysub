<div align="center">

# 省心订阅 EasySub

**自托管的订阅 / 续费 / 保号管理系统 —— 用 Telegram 提醒你按时续费，再也不怕忘记导致掉号、过期。**

[![License](https://img.shields.io/github/license/suyijun8182/easysub?color=blue)](./LICENSE)
[![Docker Pulls](https://img.shields.io/docker/pulls/suyijun8182/easysub?logo=docker)](https://hub.docker.com/r/suyijun8182/easysub)
[![Docker Image Size](https://img.shields.io/docker/image-size/suyijun8182/easysub/latest?logo=docker)](https://hub.docker.com/r/suyijun8182/easysub)
[![GitHub Release](https://img.shields.io/github/v/release/suyijun8182/easysub?logo=github)](https://github.com/suyijun8182/easysub/releases)
[![Stars](https://img.shields.io/github/stars/suyijun8182/easysub?style=social)](https://github.com/suyijun8182/easysub/stargazers)

**中文 | [English](#english) | [Русский](#русский)**

```bash
docker run -d -p 8842:8000 -v easysub_data:/app/data suyijun8182/easysub:latest
```

</div>

> 🌐 **在线体验**：<https://easysub.vviip.dpdns.org:8443/>
> 测试账号 `guest` / `guest123`；也可自行注册（需管理员审核，注册后请在 Telegram 联系管理员开通）。

---

## ✨ 功能特性

| | |
|---|---|
| 👥 **多用户** | JWT 鉴权，管理员 / 普通用户分层，数据按用户隔离，支持注册审核 |
| 💳 **订阅管理** | 周期订阅 + 一次性买断，自动计算下次续费日，到期 / 即将到期醒目提醒 |
| 📱 **保号场景** | 针对电信运营商保号：续费后从当前时间重新计算周期（无论提前还是过期续费） |
| 🔔 **多渠道通知** | **Telegram / 飞书 / QQ / Bark / Email / Pushplus / Webhook** 七种渠道，可分别启用与测试；提前天数可自定义（默认倒数 7 天每天提醒） |
| 📚 **内置服务库** | 数百个常用服务预置图标与官网（流媒体 / AI / 游戏 / VPS / **数十家电信运营商与 eSIM** 等），添加订阅时按分类浏览、直接选用 |
| 📊 **仪表盘 & 报表** | 月度 / 年度支出、支出洞察与排行、永久购买、即将续费、分类明细 |
| 🗓️ **日历视图** | 苹果风格日历，订阅一目了然 |
| 💱 **多货币** | 全球主流货币 + 自定义货币，实时汇率自动更新 |
| 🗂️ **分类管理** | 预置分类 + 自定义，支持拖拽排序 |
| 💾 **备份恢复** | 单用户 JSON 备份；管理员可一键**整站备份 / 恢复**全部成员数据（含通知配置） |
| 🛡️ **稳定自愈** | 宿主机 / 容器重启后**数据库断线自动重连**；新增列启动**自动迁移**，升级不丢数据 |
| 🌍 **多语言 / 多主题** | 中文 / English / Русский，5 套主题 |
| 🖼️ **自定义图标** | Emoji、上传图片或 URL |
| 🗄️ **接入你的 MySQL** | 不内置数据库，连接你已有的 MySQL 8，网页向导一键初始化 |

---

## 🚀 快速开始

> 镜像已发布到 **Docker Hub** 与 **GHCR**，无需源码、无需构建。
> 本项目**不内置数据库**，需准备一个可用的 **MySQL 8** 和一个空库，首次访问由网页向导引导配置。

### 方式 A：拉取镜像运行（推荐）

```bash
docker run -d --name easysub \
  -p 8842:8000 \
  -e JWT_SECRET="$(openssl rand -hex 32)" \
  -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD=admin123 \
  -e ADMIN_EMAIL=admin@example.com -e TZ=Asia/Shanghai \
  -v easysub_data:/app/data \
  --restart unless-stopped \
  suyijun8182/easysub:latest
```

或使用仓库内的 compose 文件：

```bash
docker compose -f docker-compose.hub.yml up -d
```

> 国内拉取慢可改用 GHCR 镜像：`ghcr.io/suyijun8182/easysub:latest`

启动后访问 `http://<服务器IP>:8842` → 进入「数据库安装向导」→ 填入 MySQL 连接 → 测试 → 「保存并初始化」→ 用管理员账号登录。

### 方式 B：从源码构建（自带 Caddy 自动 HTTPS）

```bash
git clone https://github.com/suyijun8182/easysub.git
cd easysub
cp .env.example .env          # 编辑 JWT_SECRET、ADMIN_* 等
vi Caddyfile                  # 可选：把 your-domain.com 改成你的域名
docker compose up -d --build
```

### 🖥️ NAS 部署

群晖 Synology / 威联通 QNAP / 飞牛 fnOS / Unraid / TrueNAS 的图形界面分步教程，详见
**[各厂家 NAS 安装教程](./各厂家NAS安装教程.md)**。

---

## 🔄 升级

数据都在**你自己的 MySQL** 里，升级只换镜像、不会丢数据；新增数据库列由程序启动时**自动迁移**（幂等）。

```bash
# 方式 A（拉取镜像部署）
docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d

# docker run 部署：拉新镜像后重建容器（保持 -v easysub_data:/app/data 与环境变量不变）
docker pull suyijun8182/easysub:latest && docker rm -f easysub && docker run -d --name easysub ... suyijun8182/easysub:latest

# 方式 B（源码构建部署）
git pull && docker compose up -d --build   # 或执行 ./update.sh
```

NAS 图形界面：在镜像里重新拉取 `latest`，再重建容器（保持 `/app/data` 映射不变）。

> 💡 **升级前先备份**：网页 **设置 → 数据备份** 导出一份 JSON；管理员可用 **整站备份** 导出全部成员数据。
> 旧版本导出的备份可安全导入新版本。

---

## ⚙️ 环境变量

| 变量 | 必填 | 说明 |
|------|:---:|------|
| `JWT_SECRET` | ✅ | 登录令牌密钥，请用 `openssl rand -hex 32` 生成随机串 |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` | ✅ | 首次初始化创建的管理员账号 |
| `TZ` | | 时区，如 `Asia/Shanghai` |
| `REMINDER_SCAN_TIME` | | 每天扫描到期订阅、发送提醒的时间，如 `09:00` |
| `TELEGRAM_BOT_TOKEN` | | 可留空，后续在网页「设置」里配置 |
| `EXCHANGE_API_BASE` / `EXCHANGE_API_URL` | | 汇率数据源（已给默认免费源） |

完整示例见 [.env.example](./.env.example)。

---

## 🧰 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI · SQLAlchemy · APScheduler |
| 前端 | Vue 3 · Vite · vue-i18n · Pinia |
| 数据库 | MySQL 8（网页向导中配置你已有的实例） |
| 部署 | Docker（多架构 amd64 / arm64）· Caddy 自动 HTTPS |

数据持久化在**你自己的 MySQL** 中；容器 `/app/data` 仅存数据库连接配置与上传的图标。

---

## 📖 使用要点

- **第一次登录**：按网页向导填 MySQL 连接（容器内不要用 `localhost`，填实际 IP / 服务名），初始化后用管理员账号登录。
- **通知渠道**：**设置 → 通知**，在 7 个标签页里配置 Telegram / 飞书 / QQ / Bark / Email / Pushplus / Webhook，每个渠道可单独启用并「测试通知」。Telegram：@BotFather `/newbot` 拿 Token → 验证机器人 → 获取 Chat ID。
- **续费规则**：点击续费后系统从当前时间重新计算下次到期（保号场景），循环订阅可选择按原到期日累加。
- **备份**：设置 → 数据备份，导出 / 导入 JSON；管理员可整站备份与恢复全部成员数据。
- **API 文档**：启动后访问 `http://<host>:8000/docs`（Swagger UI）。

更多文档：[各厂家NAS安装教程](./各厂家NAS安装教程.md) · [Docker Hub 说明](./DOCKERHUB.md) · [技术方案](./技术方案.md)

---

## ❓ 常见问题

<details>
<summary><b>数据库连接失败？</b></summary>

- 容器内不能用 `localhost`，要填 MySQL 的实际 IP / 服务名。
- 确认账号允许从容器网段远程连接，端口对局域网开放，`bind-address` 不是只绑 `127.0.0.1`。
</details>

<details>
<summary><b>如何升级而不丢数据？</b></summary>

数据都在你的 MySQL 中，升级只换镜像：
```bash
docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d
```
建议升级前先在「设置 → 数据备份」导出一份。
</details>

<details>
<summary><b>Telegram 收不到消息？</b></summary>

确认 Bot Token 正确、已和机器人对过话拿到 Chat ID；中国大陆需在设置里配置代理。
</details>

<details>
<summary><b>支持 HTTPS 吗？</b></summary>

支持。方式 B 自带 Caddy 自动签发证书，编辑 `Caddyfile` 填域名并把 DNS 解析到服务器即可。
</details>

---

## 🤝 贡献

欢迎 Issue 与 PR！Fork → 建分支 → 提交 → 发起 Pull Request，详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

仓库已配置 GitHub Actions：推送到 `main` 或打 `v*` tag 会自动构建并发布多架构镜像到 Docker Hub 和 GHCR。

## 📝 许可

[MIT License](./LICENSE)

## 📮 联系作者

Telegram [@Aiden_SU](https://t.me/Aiden_SU) · 📧 aidensu8182@gmail.com

---

<a name="english"></a>

## English

**Self-hosted subscription / renewal manager that sends Telegram reminders so you never let a subscription — or a SIM keep-alive plan — expire.**

**Highlights:** multi-user (JWT, admin/user roles) · recurring & one-time subscriptions · **7 notification channels** (Telegram / Feishu / QQ / Bark / Email / Pushplus / Webhook) · built-in service library (100s of presets incl. dozens of carriers & eSIM) · dashboard & spending reports · Apple-style calendar · multi-currency with live FX · per-user **and admin full-site** backup/restore · **auto DB reconnect** & auto-migration on upgrade · multi-language (中/EN/RU) · 5 themes · connects to **your existing MySQL 8** (no bundled DB).

```bash
docker run -d --name easysub -p 8842:8000 \
  -e JWT_SECRET="$(openssl rand -hex 32)" \
  -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD=admin123 \
  -v easysub_data:/app/data --restart unless-stopped \
  suyijun8182/easysub:latest
```

Open `http://<host>:8842` and finish the DB wizard (connect your MySQL 8). Build from source: `git clone https://github.com/suyijun8182/easysub.git && cd easysub && cp .env.example .env && docker compose up -d --build`.
NAS guides: [各厂家NAS安装教程.md](./各厂家NAS安装教程.md) · Docker Hub: [suyijun8182/easysub](https://hub.docker.com/r/suyijun8182/easysub) · License MIT · TG [@Aiden_SU](https://t.me/Aiden_SU).

---

<a name="русский"></a>

## Русский

**Самостоятельно размещаемый менеджер подписок с напоминаниями в Telegram — чтобы ни одна подписка (и SIM для поддержания номера) не истекла.**

**Возможности:** мультипользовательский режим (JWT, роли админ/пользователь) · регулярные и разовые подписки · **7 каналов уведомлений** (Telegram / Feishu / QQ / Bark / Email / Pushplus / Webhook) · встроенная библиотека сервисов (сотни пресетов, десятки операторов и eSIM) · дашборд и отчёты · календарь в стиле Apple · мультивалютность с live-курсами · резервное копирование/восстановление для пользователя **и всего сайта (админ)** · **авто-переподключение к БД** и авто-миграция при обновлении · мультиязычность (中/EN/RU) · 5 тем · подключение к **вашему MySQL 8**.

```bash
docker run -d --name easysub -p 8842:8000 \
  -e JWT_SECRET="$(openssl rand -hex 32)" \
  -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD=admin123 \
  -v easysub_data:/app/data --restart unless-stopped \
  suyijun8182/easysub:latest
```

Откройте `http://<host>:8842` и завершите мастер настройки БД (подключите ваш MySQL 8).
Инструкции для NAS: [各厂家NAS安装教程.md](./各厂家NAS安装教程.md) · Docker Hub: [suyijun8182/easysub](https://hub.docker.com/r/suyijun8182/easysub) · Лицензия MIT · TG [@Aiden_SU](https://t.me/Aiden_SU).
