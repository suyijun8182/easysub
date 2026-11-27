<div align="center">

# 省心订阅 EasySub

**自托管的订阅 / 续费 / 保号管理系统：通过 Telegram、企业微信、飞书等 14 种渠道提醒你按时续费，不再因为忘记而掉号或过期。**

[![License](https://img.shields.io/github/license/suyijun8182/easysub?color=blue)](./LICENSE)
[![Docker Pulls](https://img.shields.io/docker/pulls/suyijun8182/easysub?logo=docker)](https://hub.docker.com/r/suyijun8182/easysub)
[![Docker Image Size](https://img.shields.io/docker/image-size/suyijun8182/easysub/latest?logo=docker)](https://hub.docker.com/r/suyijun8182/easysub)
[![Latest Version](https://img.shields.io/github/v/tag/suyijun8182/easysub?sort=semver&logo=github&label=version)](https://github.com/suyijun8182/easysub/tags)
[![Stars](https://img.shields.io/github/stars/suyijun8182/easysub?style=social)](https://github.com/suyijun8182/easysub/stargazers)

**中文 | [English](#english) | [Русский](#русский)**

```bash
docker run -d --name easysub -p 8842:8000 -e EASYSUB_DB=sqlite \
  -v easysub_data:/app/data --restart unless-stopped suyijun8182/easysub:latest
```

打开 `http://<服务器IP>:8842`，注册的第一个账号就是管理员。

</div>

> 🌐 **在线体验**：<https://easysub.vviip.dpdns.org:8443/>
> 测试账号 `guest` / `guest123`，也可以自己注册，注册后直接可用。

## 🆕 v2.1.1 更新

- **修复 fake-ip 代理下通知被误拦**：用 Clash / mihomo 等 fake-ip DNS 时，Telegram 等通知不再报“请求失败，请检查地址、白名单或渠道配置”，不用再手动配置 `OUTBOUND_PRIVATE_ALLOWLIST`。
- 通知请求被安全检查拦下时，提示会写明域名、解析到的地址，以及应加入白名单的 `host:port`。

### v2.1.0

- **支持 SQLite，并设为新安装的默认数据库**：不用再准备 MySQL，一条命令就能跑起来。原来用 MySQL 的部署升级后照常运行，不用改任何配置。
- **Linux 一键安装**：一个单文件程序，不用装 Docker，支持 x86_64 和 aarch64，自动注册 systemd 服务。升级失败会自动退回旧版本。
- **修复月末续费日期漂移**：1 月 31 日的月付订阅续费后会依次变成 2/28、3/31，不会再停在 28 号。也修复了美洲等时区下续费预览比实际少一天的问题。
  已经漂移到 28 号的订阅，系统无法知道原来是几号，请手动把“下次续费日”改回正确日期一次，之后就不会再漂移。

**Android 0.3.2-alpha**：修复部分手机上顶部标题栏和同步按钮被状态栏（时间、信号、电量）遮挡的问题。0.3.1 起手机端汇率改为直接联网获取。

完整变更见 [CHANGELOG](./CHANGELOG.md)。

---

## ✨ 功能

| | |
|---|---|
| 👥 **多用户** | 管理员和普通用户分级，数据按用户隔离；开放注册，注册后直接可用（可选开启邮箱验证和管理员审核） |
| 💳 **订阅管理** | 周期订阅和一次性买断；自动计算下次续费日，月末日期不漂移；到期和即将到期醒目提示；批量续费、启用、停用、改分类、删除；可拖拽排序 |
| 📱 **保号场景** | 为运营商保号设计：续费后从当天重新计算周期，提前或过期续费都适用 |
| 🔔 **14 种通知渠道** | Telegram、飞书、QQ、Bark、Email、Pushplus、Server酱、企业微信（群机器人或自建应用）、钉钉、Discord、Slack、ntfy、Gotify、Webhook；可自定义提前天数，支持免打扰时段和每周汇总 |
| 🧪 **试用和卡片到期** | 记录试用结束日、取消截止日和付款卡有效期，到点提醒，避免被自动扣费 |
| 💰 **月度预算** | 仪表盘显示预算进度，超支时预警 |
| 📚 **内置服务库** | 数百个常用服务自带图标和官网，包括流媒体、AI、游戏、VPS、几十家运营商和 eSIM；图标随镜像发布，国内打开也很快 |
| 📊 **仪表盘和报表** | 月度和年度支出、支出排行、即将续费、分类明细，报表可导出 CSV |
| 🗓️ **日历** | 日历视图，并可生成 `.ics` 订阅链接，导入 Apple、Google、Outlook 日历 |
| 💱 **多货币** | 支持全球主流货币和自定义货币，汇率自动更新 |
| 💾 **备份和恢复** | 个人 JSON 备份、管理员整站备份和恢复、每日自动加密备份、CSV 导入导出；SQLite 额外保留最近 7 份数据库快照 |
| 🔒 **安全** | 两步验证（2FA）、API Token、登录失败限流、邮件找回密码、通知密钥加密存储 |
| 📲 **Android 客户端** | 数据保存在手机本地，可与网页版双向同步；支持到期系统通知、应用锁和后台变更提醒（Alpha 版） |
| 🔄 **稳定性** | 数据库断线后自动重连，新增字段在启动时自动迁移，升级不丢数据；网页端提示新版本 |
| 🏠 **集成** | 可安装为 PWA；`/api/integrations/summary` 接口供 Home Assistant 轮询 |
| 🎨 **界面** | 每张订阅卡片显示剩余周期条，仪表盘以续费时间轴开头，手机端使用底部标签栏；键盘和读屏可以完整操作；中文、English、Русский 三种语言，6 套主题 |

---

## 🚀 安装

有四种安装方式，按自己的情况选一种：

| 方式 | 适合 | 数据库 |
|---|---|---|
| [A. Docker + SQLite](#a-docker--sqlite推荐) | 大多数个人和家庭用户、NAS | 内置 SQLite，不需要额外安装 |
| [B. Docker + MySQL](#b-docker--mysql) | 已经有 MySQL，或需要多实例共用数据库 | 你自己的 MySQL 8 |
| [C. Linux 一键安装](#c-linux-一键安装不需要-docker) | 没有 Docker 的 VPS 或小主机 | 内置 SQLite |
| [D. 从源码构建](#d-从源码构建自带-caddy-自动-https) | 想自己改代码，或需要自动 HTTPS | 两种都可以 |

### A. Docker + SQLite（推荐）

```bash
docker run -d --name easysub \
  -p 8842:8000 \
  -e EASYSUB_DB=sqlite \
  -e TZ=Asia/Shanghai \
  -v easysub_data:/app/data \
  --restart unless-stopped \
  suyijun8182/easysub:latest
```

也可以用仓库里的 compose 文件：

```bash
docker compose -f docker-compose.sqlite.yml up -d
```

设置 `EASYSUB_DB=sqlite` 后，首次启动会自动初始化数据库，跳过安装向导。打开 `http://<服务器IP>:8842` 后注册第一个账号，它就是管理员。所有数据都保存在 `easysub_data` 数据卷里，**这个卷一定要保留**。

> 国内拉取镜像慢，可以改用 GHCR：`ghcr.io/suyijun8182/easysub:latest`

### B. Docker + MySQL

先准备一个 MySQL 8 和一个空数据库，然后：

```bash
docker compose -f docker-compose.hub.yml up -d
```

打开 `http://<服务器IP>:8842`，在安装向导中选择“MySQL”，填写连接信息，点“测试”，再点“保存并初始化”，然后注册管理员。

> 容器里不能填 `localhost`，要填 MySQL 的实际 IP 或服务名。

### C. Linux 一键安装（不需要 Docker）

```bash
curl -fsSL https://github.com/suyijun8182/easysub/releases/latest/download/install.sh | sudo bash
```

脚本会自动选择对应架构的程序，校验 SHA256 后安装为 systemd 服务，默认监听 8000 端口。安装完成后，按屏幕上显示的地址打开网页，注册第一个账号。

- **系统要求**：x86_64 或 aarch64，glibc ≥ 2.17（Debian、Ubuntu、CentOS 7 及更新版本均可）。**不支持 Alpine。**
- **自定义端口和数据目录**：`curl -fsSL …/install.sh | sudo bash -s -- --port 8842 --data /var/lib/easysub`
- **升级**：再运行一次安装命令即可，脚本会自动识别已安装的版本。新版本启动失败时会自动退回旧版本。
- **常用命令**：

  ```bash
  sudo easysub status             # 查看状态、版本、数据目录
  sudo easysub uninstall          # 卸载程序，保留数据
  sudo easysub uninstall --purge  # 连同数据一起删除（需要输入 yes 确认）
  ```

- **文件位置**：程序在 `/opt/easysub`，数据在 `/var/lib/easysub`，配置在 `/etc/easysub/easysub.env`。修改配置后执行 `sudo systemctl restart easysub`。
- **没有 systemd 或没有 root 权限**：下载 Release 里的 `easysub-linux-x86_64`（或 `aarch64`），在一个可写目录里运行 `./easysub run`，数据会保存在当前目录下的 `easysub-data/`。

### D. 从源码构建（自带 Caddy 自动 HTTPS）

```bash
git clone https://github.com/suyijun8182/easysub.git
cd easysub
cp .env.example .env   # 可选：设置强 JWT_SECRET、初始管理员等；留空时会自动生成密钥
vi Caddyfile           # 把 your-domain.com 改成你的域名
docker compose up -d --build
```

### 🖥️ NAS

群晖、威联通、飞牛 fnOS、Unraid、TrueNAS 的图形界面安装步骤，见 **[各厂家 NAS 安装教程](./各厂家NAS安装教程.md)**。新安装推荐粘贴 `docker-compose.sqlite.yml` 的内容。

---

## 🔄 升级

升级只更换程序，数据不会丢失，新增的数据库字段会在启动时自动迁移。

```bash
# Docker Compose
docker compose -f docker-compose.sqlite.yml pull && docker compose -f docker-compose.sqlite.yml up -d
# （MySQL 部署把文件名换成 docker-compose.hub.yml）

# docker run：拉取新镜像后重建容器，数据卷和环境变量保持不变
docker pull suyijun8182/easysub:latest && docker rm -f easysub && docker run -d --name easysub ... suyijun8182/easysub:latest

# Linux 一键安装：再运行一次安装命令
curl -fsSL https://github.com/suyijun8182/easysub/releases/latest/download/install.sh | sudo bash

# 源码部署
git pull && docker compose up -d --build
```

> 💡 **升级前先备份**：在网页“设置 → 数据备份”导出一份 JSON，管理员可以导出整站备份。旧版本的备份可以直接导入新版本。

### 从 MySQL 换成 SQLite

1. 在旧实例中，用管理员账号到“设置 → 数据备份”导出**整站备份**，记住备份密码。
2. 用方式 A 或 C 新建一个 SQLite 实例（**使用新的数据卷或数据目录**），注册管理员。
3. 在新实例的“设置 → 数据备份”中导入整站备份，核对账号、订阅、分类和通知设置。
4. 确认无误后，把访问入口切换到新实例。旧实例先保留一段时间，以便回退。

上传过的自定义图标不包含在备份里，需要把旧实例 `data/icons` 目录复制到新实例。Android 客户端在切换后需要重新同步一次。

---

## ⚙️ 环境变量

都是可选项。

| 变量 | 说明 |
|---|---|
| `EASYSUB_DB` | 设为 `sqlite` 时，首次启动自动初始化 SQLite，跳过安装向导；已有数据库配置时不起作用 |
| `JWT_SECRET` | 登录令牌密钥（可用 `openssl rand -hex 32` 生成）。不设置时会自动生成并保存在 `data/jwt_secret`，所以必须保留数据卷 |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` | 预置管理员账号。不设置密码时，第一个注册的账号就是管理员 |
| `BACKUP_PASSWORD` | 每日自动备份的加密密码，至少 12 位；留空则不做自动备份 |
| `TZ` | 时区，例如 `Asia/Shanghai` |
| `REMINDER_SCAN_TIME` | 每天检查到期并发送提醒的时间，默认 `09:00` |
| `REQUIRE_ADMIN_APPROVAL` | 新用户注册后是否需要管理员审核，默认 `false` |
| `OUTBOUND_PRIVATE_ALLOWLIST` | 允许通知请求访问的内网地址，例如 `nas.lan:5000,192.168.1.10:7890` |
| `TELEGRAM_BOT_TOKEN` | 可以留空，之后在网页设置中填写 |
| `EXCHANGE_API_BASE` / `EXCHANGE_API_URL` | 汇率数据源，已有默认的免费源 |

完整示例见 [.env.example](./.env.example)。

---

## 📖 使用说明

- **通知渠道**：在“设置 → 通知”中，每个渠道都可以单独启用并发送测试通知，也可以设置免打扰时段和每周汇总。
  企业微信支持两种模式：**群机器人**（只要一个 Webhook 地址），以及**自建应用**（填写企业 ID、应用 ID、Secret，可指定成员、部门或标签，配合微信插件可以直接在微信里收到提醒）。面板中附有取值步骤、可信 IP 说明和反向代理示例。
- **续费的两种方式**：
  - **从今天起算**：适合保号，从当天重新计算一个周期。
  - **常规循环**：从原到期日往后加一个周期，提前续费不会损失已付的时间。月末日期会保持在原来的日子，例如 31 号的订阅遇到 2 月会变成 28 号（闰年为 29 号），下个月再回到 31 号。
- **批量操作和排序**：在订阅页点“多选”可以批量操作，点“排序”可以调整顺序，也可以直接拖拽。
- **安全**：在设置中可以开启两步验证、创建 API Token（供脚本或 Home Assistant 使用）。找回密码需要管理员先配置 SMTP。
- **Android 客户端**：从 [Releases](https://github.com/suyijun8182/easysub/releases) 下载 APK。在 App 的“账号与同步”中填写服务器地址和账号即可双向同步。说明见 [Android 0.3.2](docs/android-0.3.2.md)。
- **API 文档**：启动后访问 `http://<服务器IP>:<端口>/docs`。

---

## ❓ 常见问题

<details>
<summary><b>应该选 SQLite 还是 MySQL？</b></summary>

个人和家庭使用选 SQLite 就够了：不用额外安装数据库，备份时只需保留一个数据卷。如果你已经有 MySQL，或者要让多个实例共用一个数据库，再选 MySQL。之后也可以通过整站备份在两者之间迁移。
</details>

<details>
<summary><b>MySQL 连接失败？</b></summary>

- 容器里不能用 `localhost`，要填 MySQL 的实际 IP 或服务名。
- 确认这个账号允许从容器所在网段远程连接，并且 MySQL 的 `bind-address` 不是只绑定了 `127.0.0.1`。
</details>

<details>
<summary><b>月付订阅的续费日从 31 号变成了 28 号？</b></summary>

这是 v2.1.0 之前的问题。升级后，请把这条订阅的“下次续费日”手动改回正确日期一次，之后就不会再漂移了。
</details>

<details>
<summary><b>Linux 一键安装提示“不支持 Alpine”或 glibc 版本太低？</b></summary>

安装包里的 Python 运行时需要 glibc 2.17 或更高版本，而 Alpine 使用的是 musl。这种情况请改用 Docker 部署。
</details>

<details>
<summary><b>Telegram 收不到消息？</b></summary>

确认 Bot Token 正确，并且已经和机器人对话过、获取了 Chat ID。在中国大陆需要在设置中配置代理。
</details>

<details>
<summary><b>支持 HTTPS 吗？</b></summary>

支持。方式 D 自带 Caddy，会自动申请证书：在 `Caddyfile` 中填写域名，并把域名的 DNS 解析到服务器即可。其他方式可以放在你自己的反向代理后面。
</details>

---

## 🧰 技术栈

| 组件 | 技术 |
|---|---|
| 后端 | FastAPI · SQLAlchemy · APScheduler |
| 前端 | Vue 3 · Vite · vue-i18n · Pinia |
| 数据库 | SQLite（默认）或 MySQL 8 |
| Android | Capacitor（数据保存在手机本地，可选同步） |
| 部署 | Docker（amd64 / arm64）· Linux 单文件安装器（Rust）· Caddy 自动 HTTPS |

## 🤝 贡献

欢迎提交 Issue 和 PR，详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

推送到 `main` 或打 `v*` tag 后，GitHub Actions 会自动构建多架构镜像并发布到 Docker Hub 和 GHCR，同步 Docker Hub 页面说明，创建 GitHub Release，并编译 Linux 安装包。

## 📝 许可

[MIT License](./LICENSE)

## 📮 联系作者

Telegram [@Aiden_SU](https://t.me/Aiden_SU) · 📧 aidensu8182@gmail.com

---

<a name="english"></a>

## English

**A self-hosted subscription and renewal manager. It reminds you over 14 channels (Telegram, WeCom, Feishu, Email, ntfy, Webhook and more), so no subscription or SIM keep-alive plan expires unnoticed.**

**New in v2.1.1:** notifications such as Telegram are no longer blocked when a Clash / mihomo fake-ip DNS resolves them into 198.18.0.0/15, and a blocked request now says which host, address and allowlist entry are involved. **New in v2.1.0:** SQLite is now the default database, so no MySQL is needed (existing MySQL setups keep working) · a one-command Linux installer that needs no Docker (x86_64 / aarch64, systemd, upgrades that roll back on failure) · month-end renewals stay on their day (Jan 31 → Feb 28 → Mar 31), and the renewal preview no longer shows a day early in time zones west of UTC. **Android 0.3.2-alpha:** the top bar and sync button are no longer hidden under the status bar on some phones; since 0.3.1 the phone fetches exchange rates online by itself.

**Features:** multi-user with open sign-up · recurring and one-time subscriptions with bulk actions and drag reordering · 14 notification channels with quiet hours and a weekly digest · trial, cancel-by and card-expiry tracking · monthly budget · built-in library of hundreds of services · dashboard, reports and CSV export · calendar with an `.ics` feed · multi-currency with live exchange rates · personal and full-site backups plus daily encrypted auto-backups · 2FA, API tokens and encrypted secrets · Android app (local-first, optional two-way sync) · PWA · Home Assistant endpoint · Chinese, English and Russian · 6 themes.

```bash
# Docker + SQLite (recommended), then open http://<host>:8842
docker run -d --name easysub -p 8842:8000 -e EASYSUB_DB=sqlite \
  -v easysub_data:/app/data --restart unless-stopped suyijun8182/easysub:latest

# Linux without Docker (glibc ≥ 2.17, not Alpine), listens on port 8000
curl -fsSL https://github.com/suyijun8182/easysub/releases/latest/download/install.sh | sudo bash
```

Register after opening the page. The first account becomes the administrator. Keep the data volume, which also holds the auto-generated JWT key. To use your own MySQL 8 instead, run `docker compose -f docker-compose.hub.yml up -d` and choose MySQL in the setup wizard. If a monthly renewal date already drifted to the 28th before v2.1.0, set the correct date once by hand.

NAS guides: [各厂家NAS安装教程.md](./各厂家NAS安装教程.md) · Docker Hub: [suyijun8182/easysub](https://hub.docker.com/r/suyijun8182/easysub) · [Changelog](./CHANGELOG.md) · MIT License · TG [@Aiden_SU](https://t.me/Aiden_SU)

---

<a name="русский"></a>

## Русский

**Самостоятельно размещаемый менеджер подписок и продлений. Напоминает о продлении по 14 каналам (Telegram, WeCom, Feishu, Email, ntfy, Webhook и др.), чтобы ни одна подписка и ни одна SIM-карта не истекла незаметно.**

**Новое в v2.1.1:** уведомления (например, Telegram) больше не блокируются, когда fake-ip DNS Clash / mihomo отдаёт адрес из 198.18.0.0/15, а при блокировке запроса сообщение называет хост, адрес и нужную запись белого списка. **Новое в v2.1.0:** SQLite стал базой данных по умолчанию, MySQL больше не нужен (существующие установки с MySQL продолжают работать) · установка на Linux одной командой без Docker (x86_64 / aarch64, systemd, автоматический откат при неудачном обновлении) · даты продления в конце месяца больше не сдвигаются (31.01 → 28.02 → 31.03), а предпросмотр продления больше не показывает дату на день раньше в часовых поясах западнее UTC. **Android 0.3.2-alpha:** верхняя панель и кнопка синхронизации больше не скрываются под строкой состояния на некоторых телефонах; с 0.3.1 телефон сам загружает курсы валют из сети.

**Возможности:** несколько пользователей и открытая регистрация · регулярные и разовые подписки, массовые действия, сортировка перетаскиванием · 14 каналов уведомлений, тихие часы и еженедельная сводка · отслеживание пробного периода и срока действия карты · месячный бюджет · библиотека из сотен сервисов · дашборд, отчёты и экспорт в CSV · календарь и ссылка `.ics` · мультивалютность · резервные копии пользователя и всего сайта, ежедневные зашифрованные копии · 2FA, API-токены, шифрование секретов · приложение для Android (данные на телефоне, синхронизация по желанию) · PWA · интеграция с Home Assistant · интерфейс на китайском, английском и русском · 6 тем.

```bash
# Docker + SQLite (рекомендуется), затем откройте http://<host>:8842
docker run -d --name easysub -p 8842:8000 -e EASYSUB_DB=sqlite \
  -v easysub_data:/app/data --restart unless-stopped suyijun8182/easysub:latest

# Linux без Docker (glibc ≥ 2.17, Alpine не поддерживается), порт 8000
curl -fsSL https://github.com/suyijun8182/easysub/releases/latest/download/install.sh | sudo bash
```

После открытия страницы зарегистрируйтесь: первая учётная запись получает права администратора. Сохраняйте том данных: в нём же лежит автоматически созданный ключ JWT.

Инструкции для NAS: [各厂家NAS安装教程.md](./各厂家NAS安装教程.md) · Docker Hub: [suyijun8182/easysub](https://hub.docker.com/r/suyijun8182/easysub) · [История изменений](./CHANGELOG.md) · Лицензия MIT · TG [@Aiden_SU](https://t.me/Aiden_SU)
