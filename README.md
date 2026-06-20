# 省心订阅 EasySub
不删档测试地址
https://easysub.vviip.dpdns.org:8443/
1.测试帐号  guest   guest123
2.可自己注册帐号  需要管理员审核 请TG提醒管理

<div align="center">

**[中文](#-省心订阅-easysub) | [English](#english-version) | [Русский](#русская-версия)**

自托管的订阅 / 续费 / 保号管理系统，通过 **Telegram** 提醒你及时续费保号，防止忘记导致项目过期。

[🚀 快速开始](#快速开始) • [📖 文档](#文档) • [💡 功能](#功能特性) • [🤝 贡献](#贡献) • [📝 许可](#许可)

</div>

---

## 功能特性

- ✅ **多用户系统** - JWT 鉴权，管理员和普通用户分层
- ✅ **订阅管理** - 支持周期订阅和一次性买断
- ✅ **多语言** - 中文 / English / Русский
- ✅ **多主题** - 浅色 / 深色 / 海洋 / 森林 / 紫罗兰主题
- ✅ **多货币** - 全球主流货币，实时汇率，可自定义
- ✅ **仪表盘** - 月度/年度支出统计，即将到期提醒，支出分析
- ✅ **分类管理** - 流媒体 / AI / 游戏 / VPS / 电信运营商等，支持自定义
- ✅ **日历视图** - 苹果风格日历，一目了然
- ✅ **报表分析** - 支出洞察、排行榜、永久购买、即将续费
- ✅ **Telegram 通知** - 自动提醒，支持自定义提前天数
- ✅ **自定义图标** - Emoji 或上传图片
- ✅ **本地数据库** - 连接你已有的 MySQL，无需额外部署

## 技术栈

| 组件 | 技术 |
|------|------|
| **后端** | FastAPI + SQLAlchemy + APScheduler |
| **前端** | Vue 3 + Vite + vue-i18n |
| **数据库** | MySQL 8（由用户在网页向导中配置） |
| **部署** | Docker Compose + Caddy（自动 HTTPS） |

> **重要**: 数据库连接在网页「安装向导」中配置，首次访问会自动引导。

---

## 快速开始

### 前置要求
- Docker & Docker Compose（推荐）或 Python 3.11+ / Node.js 18+
- 已有的 MySQL 8 实例 + 一个空数据库

### Docker 一键部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/easysub.git
cd easysub

# 2. 准备配置文件
cp .env.example .env
# 编辑 .env，改以下内容：
#   - JWT_SECRET: 用 `openssl rand -hex 32` 生成
#   - ADMIN_USERNAME/ADMIN_PASSWORD: 管理员账号密码
#   - TELEGRAM_BOT_TOKEN: 可先留空，后续在网页设置

# 3. 配置域名（可选，本地测试可跳过）
vi Caddyfile  # 把 your-domain.com 改成你的域名

# 4. 启动服务
docker compose up -d --build

# 5. 首次访问
#    访问 http://服务器IP  或  https://你的域名
#    会进入「数据库安装向导」
#    填入你的 MySQL 连接信息并测试连接
#    点「保存并初始化」自动建表和创建管理员
```

### 本地开发部署

**后端**（需要 Python 3.11+）：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

**前端**（需要 Node.js 18+）：

```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

### NAS 用户部署

如果你使用 TrueNAS / 飞牛 fnOS / 群晖 / 威联通 / Unraid，详见 [安装部署文档](./安装部署文档.md)

---

## 文档

| 文档 | 说明 |
|------|------|
| [README.md](./README.md) | 项目概览（本文件） |
| [安装部署文档.md](./安装部署文档.md) | NAS 和 Docker 详细部署 |
| [技术方案.md](./技术方案.md) | 项目架构和技术选型 |
| [升级与GitHub指南.md](./升级与GitHub指南.md) | 版本升级和同步到个人 GitHub 仓库 |

---

## 使用指南

### 第一次登录

1. **访问应用** - 打开浏览器访问部署地址
2. **数据库配置** - 首次进入会显示安装向导：
   - 输入 MySQL 主机地址（不要用 localhost）
   - 输入端口、用户名、密码、数据库名
   - 点「测试连接」验证
   - 点「保存并初始化」自动建表和创建管理员
3. **登录** - 用 `.env` 中的 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 登录

### Telegram 机器人配置

1. 在 Telegram 中找 **@BotFather**
2. 发送命令 `/newbot` 创建新机器人
3. 按提示输入机器人名称和用户名，获得 **Bot Token**
4. 回到应用，**设置** → **Telegram 配置**
5. 填入 Bot Token，点「验证机器人」
6. 给机器人发一条消息，点「获取 Chat ID」
7. 保存配置，点「发送测试」验证

之后系统会在续费日前根据设置自动提醒。

### 添加订阅

1. 点「新增订阅」
2. 填写订阅信息：
   - 名称和图标
   - 分类、付款方式
   - 金额和货币
   - 周期（按月/年/其他）和开始日期
   - 自动续订选项
3. 保存

系统会根据周期和开始日期自动计算下次续费日期。

### 查看报表

**仪表盘** - 总览当月/年支出和即将到期项目
**日历** - 以日历形式查看所有订阅
**报表** - 详细的支出分析和趋势

---

## 主要功能清单

| 功能 | 状态 | 说明 |
|------|------|------|
| 多用户管理 | ✅ | 支持管理员和普通用户 |
| 订阅CRUD | ✅ | 完整的增删改查 |
| 自动续费提醒 | ✅ | Telegram 推送 |
| 多货币 | ✅ | 实时汇率、自定义货币 |
| 多语言 | ✅ | 中 / 英 / 俄 |
| 多主题 | ✅ | 5 个主题可选 |
| 分类管理 | ✅ | 预置 + 自定义分类 |
| 日历视图 | ✅ | 苹果风格日历 |
| 报表分析 | ✅ | 支出统计和趋势分析 |
| 组合包 | ✅ | 支持打包多个订阅 |
| 家庭共享 | ⚒️ | 开发中 |

---

## 目录结构

```
easysub/
├── backend/
│   ├── app/
│   │   ├── main.py              应用入口
│   │   ├── models.py            数据模型
│   │   ├── schemas.py           API 数据结构
│   │   ├── config.py            配置管理
│   │   ├── database.py          数据库连接
│   │   ├── security.py          鉴权和密码
│   │   ├── routers/             API 路由
│   │   │   ├── auth.py          认证
│   │   │   ├── subscriptions.py 订阅管理
│   │   │   ├── reports.py       报表
│   │   │   └── ...
│   │   └── services/            业务服务
│   │       ├── telegram.py      Telegram 机器人
│   │       ├── exchange.py      汇率服务
│   │       └── scheduler.py     定时任务
│   ├── requirements.txt         Python 依赖
│   └── .env.example             环境变量示例
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── views/               页面组件
│   │   ├── components/          可复用组件
│   │   ├── api/                 API 接口封装
│   │   ├── stores/              Pinia 状态
│   │   ├── i18n/                国际化配置
│   │   └── styles/              样式
│   ├── package.json
│   └── vite.config.js
├── Dockerfile                   多阶段构建
├── docker-compose.yml           生产配置
├── docker-compose.fnos.yml      NAS 简化配置
├── Caddyfile                    反向代理配置
├── .env.example                 环境变量示例
└── README.md                    本文件
```

---

## 环境变量说明

```bash
# JWT 密钥（必改）
JWT_SECRET=your-random-secret-key

# 数据库初始化时创建的管理员
ADMIN_USERNAME=admin
ADMIN_PASSWORD=password
ADMIN_EMAIL=admin@example.com

# Telegram 机器人（可后续在网页设置）
TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_PROXY=          # 可选：TG API 代理
TELEGRAM_BOT_HTTP_PROXY=     # 可选：HTTP 代理

# 汇率 API（默认免费）
EXCHANGE_API_BASE=USD
EXCHANGE_API_URL=https://open.er-api.com/v6/latest/

# 定时任务扫描时间
REMINDER_SCAN_TIME=09:00

# 时区
TZ=Asia/Shanghai
```

详见 `.env.example`

---

## 自动构建与镜像发布

本仓库包含 GitHub Actions 工作流，会在推送到 `main` 分支或创建 tag（如 `v1.0.1`）时自动构建并推送镜像到 Docker Hub 和 GitHub Container Registry (GHCR)。

步骤：

1. 在 Docker Hub 创建仓库（例如 `suyijun8182/easysub`）。
2. 在 Docker Hub 创建 access token：登录 https://hub.docker.com → Account Settings → Security → New Access Token，复制 token（只显示一次）。
3. 在 GitHub 仓库设置中添加 Secrets（Settings → Secrets and variables → Actions）：
   - `DOCKERHUB_USERNAME`：你的 Docker Hub 用户名
   - `DOCKERHUB_TOKEN`：上一步生成的 access token
4. （可选）GHCR：Actions 会使用 `GITHUB_TOKEN` 自动推送到 `ghcr.io/${{ github.repository_owner }}/easysub`，通常无需额外 secret，但请确保仓库 Actions 权限允许写入 Packages（Settings → Actions → General）。
5. 触发构建：在本地创建并推送 tag，或在 GitHub Actions 页面手动运行工作流。

示例：在本地创建并推送 tag 会触发构建并把镜像推到两个仓库：

```bash
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

构建完成后将生成：
- `suyijun8182/easysub:v1.0.1` 和 `suyijun8182/easysub:latest`（Docker Hub）
- `ghcr.io/<your-org-or-username>/easysub:v1.0.1` 和 `ghcr.io/<your-org-or-username>/easysub:latest`（GHCR）

若需我替你把镜像直接推到 Docker Hub，我也可以在本地构建并推送（需要你提供 Docker Hub token，或在本地先执行 `docker login`）。


## 常见问题（FAQ）

**Q: 数据库连接失败？**
- 确保 MySQL 实例可访问，检查防火墙
- 容器内不能用 `localhost`，用 MySQL 实际 IP 或服务名
- 检查用户名/密码/库名拼写

**Q: Telegram 机器人无法接收消息？**
- 确认 Bot Token 正确
- 检查机器人是否正确创建
- 若在中国大陆，需要配置代理

**Q: 如何升级而不丢失数据？**
- 所有数据存储在你的 MySQL 中
- 运行 `./update.sh` 或 `git pull && docker compose up -d --build`
- 数据库会自动迁移

**Q: 支持 HTTPS 吗？**
- 是的，使用 Caddy 自动配置 HTTPS
- 编辑 `Caddyfile` 填入你的域名
- DNS 需解析到服务器

**Q: 可以导入/导出订阅吗？**
- 目前支持通过 API
- 计划在未来版本中添加 UI

---

## API 文档

启动后访问 `http://localhost:8000/docs` 查看完整 API 文档（Swagger UI）

常用端点：
- `POST /api/auth/login` - 登录
- `GET/POST /api/subscriptions` - 订阅列表/创建
- `GET /api/dashboard` - 仪表盘数据
- `GET /api/reports/...` - 报表数据

---

## 贡献

欢迎贡献代码、报告问题或提建议！

1. **Fork** 项目
2. **创建功能分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送分支** (`git push origin feature/AmazingFeature`)
5. **开启 Pull Request**

详见 [CONTRIBUTING.md](./CONTRIBUTING.md)

---

## 许可

本项目采用 [MIT License](./LICENSE) 许可证。

---

## 支持

- 📧 Email: [提交 Issue]
- 🐛 Bug Report: [Issues]
- 💬 讨论: [Discussions]

---

## 致谢

感谢所有贡献者和使用者的支持！

---

# English Version

## EasySub - Self-hosted Subscription Management

A self-hosted subscription management system that sends **Telegram** reminders to keep your subscriptions from expiring.

### Features

- ✅ Multi-user with JWT authentication
- ✅ Multi-language (Chinese / English / Russian)
- ✅ Multiple themes
- ✅ Multi-currency with real-time exchange rates
- ✅ Dashboard with spending analytics
- ✅ Category management
- ✅ Calendar and report views
- ✅ Telegram notifications
- ✅ Recurring and one-time subscriptions
- ✅ Custom icons

### Quick Start

```bash
# Clone
git clone <repo-url>
cd easysub

# Copy config
cp .env.example .env

# Start
docker compose up -d --build

# Access at http://localhost
```

For full English documentation, see [安装部署文档.md](./安装部署文档.md)

---

# Русская версия

## EasySub - Система управления подписками

Система управления подписками с уведомлениями в Telegram.

### Возможности

- ✅ Мультипользовательская система
- ✅ Поддержка русского языка
- ✅ Множественные валюты
- ✅ Уведомления о возобновлении
- ✅ Аналитика расходов

### Быстрый старт

```bash
git clone <repo-url>
cd easysub
cp .env.example .env
docker compose up -d --build
```

Полная документация доступна в [安装部署文档.md](./安装部署文档.md)
