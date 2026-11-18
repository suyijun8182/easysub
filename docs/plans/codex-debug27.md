# EasySub debug27：月末续费漂移、SQLite 支持、Linux 一键部署（Rust）

> 制定日期：2026-11-18。执行者：Codex。来源：`需要实现的功能.txt` 中的 debug27。
> 当前线上版本为 v2.0.2，Android 0.3.0-alpha。

分三个阶段，**按顺序一次做完，中途不要停下来等确认**，最后合并发布为 **v2.1.0**。每个阶段至少提交一次 commit，提交前该阶段的验证命令必须通过；某个阶段被卡住时，先记下原因，能继续的部分继续做，最后在报告里说明。

## 本机环境（已核实）

- **后端测试必须使用** `D:/Claude/easysub/backend/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`。这个环境里已经装好 requirements.txt 的全部依赖和 pytest，基线结果为 68 passed / 27 skipped。**不要执行 pip install**，因为沙箱内访问 PyPI 会报 SSL 错误。如果确实缺少某个包，在报告里写明，不要绕过。
- 前端依赖已经安装在 `frontend/node_modules`。**不要执行 npm install 或 npm ci**，直接运行 npm scripts 和 `node --test`。
- Rust 依赖已经预先下载到 cargo 缓存，`x86_64-unknown-linux-musl` 目标也已安装。所有 cargo 命令都要加 `--offline`。
- 阶段 3 中 python-build-standalone 的下载和打包只在 CI 中进行，本地不要下载。
- 如果 `backend/.pytest_cache` 无法写入，请忽略（已经用 `-p no:cacheprovider` 规避）。

- Windows 10，可用工具：Python 3.12、Node、cargo 1.99、git。**没有 Docker，也没有可用的 WSL 发行版。**
- 因此阶段 3 本地只做以下几件事：执行 `cargo test`（单元测试要写成在 Windows 上也能运行，把 Linux 专有的调用，比如 systemctl、chown、useradd，抽象成 trait 再 mock 掉）；执行 `rustup target add x86_64-unknown-linux-musl`，再用 `cargo check --target x86_64-unknown-linux-musl` 检查能否编译；workflow 和 install.sh 写好后，能做哪些静态检查就做哪些（例如 `bash -n`；如果有 shellcheck、actionlint 也跑一下）。CI 冒烟测试和 systemd 集成测试在本地**跑不了**，报告里要如实写“未执行”，不要声称已经通过。

## 通用约束

- 工作目录：worktree `D:/Claude/easysub-debug27`（分支 `feat/debug27`，已由 Claude 创建）。不要修改 `D:\Claude\easysub`。
- 不 push，不打 tag，不发 Release，不在 GitHub 上评论。
- 后端每个修复先写一个会失败的测试，测试风格参照 `backend/tests/test_static_safety.py`。前端的纯函数测试放在已有的 `node --test` 体系里。
- 所有说明文字和提示文案用中文，i18n 文件必须同步（`npm run i18n:check` 要通过）。
- 每次更新都要同时更新 CHANGELOG、README 和 DOCKERHUB.md 顶部的版本说明（项目惯例）。

---

## 阶段 1：月付遇到月末时续费日期漂移

### 现象

新建一条月付记录，下次续费日设为 2027-01-31，连续两次用“常规循环”（`mode=due`）续费，保存后的日期依次是 2/28、3/28，没有回到 3/31。另外，浏览器时区设为 America/Los_Angeles 时，第二次续费弹窗的预览显示 3/27，实际保存的是 3/28。

### 根因（已核实）

1. **没有记录“锚定日”**：`backend/app/routers/subscriptions.py:233-234` 的 due 模式直接计算 `add_cycle(sub.next_renewal_date, ...)`。1/31 加一个月被截断成 2/28 以后，“31 号”这个信息就丢了，之后每个月都会从 28 号继续往后推。`billing._add_months` 本身没有错，问题在于原始的日只存在于上一次的日期里。
2. **前端按 UTC 解析日期**：`frontend/src/views/Subscriptions.vue:548` 的 `new Date(dateStr)` 和 `:905` 的 `new Date(renewTarget.value.next_renewal_date)`，会把 `'2027-02-28'` 按 **UTC 零点**解析。在 UTC−8 时区，`getDate()` 得到的是 27 号，所以预览显示 3/27。`:563` 的 `new Date().toISOString().slice(0,10)` 也有同样的问题：在 UTC+8 的凌晨，默认开始日期会变成前一天。
3. Android 端 `frontend/src/android-preview/store.js:183` 的离线续费逻辑同样没有锚定日（它按 UTC 正午解析，所以没有时区问题，但月末漂移的问题依然存在）。

### 设计

在订阅上新增 `billing_anchor_day`（可空的小整数，取值 1–31），表示“按月或按年计费时，每期本来应该落在几号”。

- **写入时机**：
  - 新建订阅：取 `next_renewal_date.day`。如果用户没填、由后端推算，就取 `start_date.day`。
  - 编辑订阅：**只有当 `next_renewal_date` 的值确实变了**时才更新为新日期的 day。前端表单每次都会把所有字段提交上来，如果不判断是否变化，已经漂移到 28 号的数据会把锚定日也覆盖成 28。
  - `mode=today` 续费：锚定日设为今天的 day。
  - `mode=due` 续费：锚定日保持不变。
  - CSV 导入和备份导入：如果备份里有这个字段就用备份里的值，没有就按新建订阅的规则处理。
  - 计费周期从 month/year 改为 day/week 时，锚定日设为 NULL。
- **计算**：`billing.add_cycle(d, cycle, count, anchor_day=None)`。对 month/year 周期，先算出目标年月，再取 `min(anchor_day or d.day, 当月天数)`。day/week 周期忽略锚定日。`compute_next_renewal` 也要传入锚定日，确保反复推进日期时不会漂移。
- **旧数据**：旧数据的锚定日为 NULL，计算时退回使用 `d.day`。已经漂移到 28 号的数据无法自动恢复（真实的日已经丢失），**不要猜测并改写旧数据**。在 CHANGELOG 里说明：受影响的订阅需要手动把下次续费日改回正确日期一次，改完以后就不会再漂移。
- **数据库迁移**：在 `migrate._COLUMNS` 中追加 `("subscriptions", "billing_anchor_day", "SMALLINT NULL")`。
- **Schema**：`SubscriptionIn`、`SubscriptionUpdate`、`SubscriptionOut` 都加上这个字段（可选）。确认 `services/sync.py:303` 的未知字段校验能放行它，并且 Android 0.3.0 的旧客户端不带这个字段时同步依然正常（不带字段时表示“不修改”，不能被当成 NULL 写回去）。
- **前端**：
  - `Subscriptions.vue` 中删除 `addMonths`、`addCycle`、`toISO` 这几个基于 `Date` 的实现，新建 `frontend/src/billing-date.js`，导出 `parseYMD`、`formatYMD`、`todayYMD()`（按本地时区）、`addCycle(ymd, cycle, count, anchorDay)`。这些函数内部只做整数年月日运算，不经过 `Date` 的时区换算。
  - 续费预览、表单自动推算、默认开始日期都改用这个模块。due 模式的预览要传入 `renewTarget.billing_anchor_day`。
  - Android 的 `store.js` 改为调用同一个模块（或者保持同一套算法），离线续费时同样维护锚定日。
- **批量续费**：如果存在批量续费接口或前端逻辑，用同样的规则处理（执行时先 `grep -n "bulk" Subscriptions.vue` 确认）。

### 必须新增的测试

后端（`backend/tests/test_billing_anchor.py`）：
- 1/31 续费两次（due 模式）→ 2/28，然后 3/31。
- 闰年：2028-01-31 续费 → 2/29，然后 3/31；年付 2028-02-29 续费 → 2029-02-28，然后 2030-02-28。年付的锚定日只用来恢复日（2/29 → 2/28 → 下一个闰年回到 2/29），月份不变。
- 编辑时只修改备注、不修改 `next_renewal_date`，锚定日保持不变；修改 `next_renewal_date` 时，锚定日随之更新。
- 旧数据（锚定日为 NULL）续费后的行为与现在一致。
- 通过 sync 推送一条不带 `billing_anchor_day` 的订阅时，服务端已有的锚定日不会被清空。

前端（`frontend/src/billing-date.test.js`，并加进 `package.json` 的测试脚本）：
- 设置 `process.env.TZ = 'America/Los_Angeles'` 和 `'Asia/Shanghai'` 各跑一遍：`addCycle('2027-02-28','month',1,31) === '2027-03-31'`，`addCycle('2027-01-31','month',1) === '2027-02-28'`。
- 在两个时区下，`todayYMD()` 都应与本地日历日期一致。

### 验证

```bash
cd backend && python -m pytest -q
cd ../frontend && npm run i18n:check && npm run test:android-preview && node --test src/billing-date.test.js && npm run build
```

手动验证：在 Chrome DevTools → Sensors 中把时区设为 America/Los_Angeles，新建 2027-01-31 的月付订阅，连续两次常规循环续费。每次弹窗的预览日期要和保存后的日期一致，最后一次是 3/31。

### 版本

这个阶段先不改版本号，统一在阶段 3 改成 2.1.0。在 CHANGELOG 的 2.1.0 条目中写明修复内容，并加上说明：已经漂移的订阅需要手动修正一次。

---

## 阶段 2：支持 SQLite（v2.1.0 的一部分）

### 现状（已核实）

- ORM 全部基于 SQLAlchemy 2，测试本来就跑在 SQLite 上。真正绑定 MySQL 的地方只有以下几处：
  - `bootstrap.build_url` 写死了 `mysql+pymysql`，`test_connection` 执行的是 `SELECT VERSION()`；
  - `setup.DBConfig` 要求必须填 host/user/database；
  - `migrate.run_migrations` 遇到非 MySQL 数据库会直接 return，导致 SQLite 的旧库以后**无法补列**（阶段 1 新增的列就会遇到这个问题）；
  - `database.init_engine` 中的 MySQL 专用参数（已经按方言判断过）；
  - `models.py` 的 `LONGTEXT` variant（已经有 `with_variant`，SQLite 下不受影响）。
- 运行时是 uvicorn 单进程，加上 APScheduler 在同一个进程里，适合使用 SQLite。

### 任务

1. **配置格式**：`db_config.json` 新增 `engine` 字段，取值为 `"sqlite"` 或 `"mysql"`。没有这个字段的旧配置一律当作 MySQL（老用户升级后行为不变）。SQLite 的配置为 `{"engine":"sqlite","path":"data/easysub.db"}`。`path` 必须位于 `data/` 目录内，校验时用 realpath 加 commonpath，拒绝 `..` 和绝对路径。
2. **`bootstrap`**：
   - `build_url` 按 engine 分支处理；
   - SQLite 的 `test_connection` 要检查目录可写，打开数据库执行 `select sqlite_version()` 后再关闭；
   - `save_config` 的白名单字段加上 `engine`、`path`。
3. **`database.init_engine`**：对 SQLite 设置 `connect_args={"check_same_thread": False, "timeout": 30}`，并通过 `event.listens_for(engine, "connect")` 执行 `PRAGMA journal_mode=WAL`、`foreign_keys=ON`、`busy_timeout=30000`、`synchronous=NORMAL`。SQLite 不需要 `pool_recycle`。注意：开启 `foreign_keys=ON` 后，删除订阅时需要先删 `NotificationLog`（`subscriptions.py:288` 已经这样做了），要用测试覆盖。
4. **迁移改成与方言无关**：`_column_exists` 和 `_table_exists` 改用 `sqlalchemy.inspect(conn)`。在 `_COLUMNS` 的列定义里，`TINYINT(1)` 和 `DOUBLE` 在 SQLite 下需要映射（建议 `_COLUMNS` 只写类型名，按方言渲染；或者给 SQLite 单独维护一张映射表）。`sync_records` 等表中 MySQL 专用的类型修正，只在 MySQL 下执行。
5. **安装向导（前端）**：第一步选择数据库类型。“SQLite（推荐，免安装，适合个人和家庭）”为默认选项，选择后不需要填写任何内容。选择“MySQL（已有 MySQL 或多实例）”时显示原来的表单。`DBConfig` 改为按 engine 区分的 discriminated union。
6. **无界面自动配置**（阶段 3 和 Docker 都会用到）：如果启动时没有 `db_config.json`，并且环境变量 `EASYSUB_DB=sqlite`，就自动写入 SQLite 配置并完成初始化，跳过安装向导。没有设置这个环境变量时，行为保持不变。
7. **从 MySQL 迁移到 SQLite**：不写新的迁移工具，复用现有的“完整备份导出/导入”。新增一个测试：把 MySQL 形态的备份 fixture（可以用 `backend/tests/fixtures` 里已有的，或者 `easysub-backup-2026-10-14.json` 脱敏后的版本）导入到全新的 SQLite 库，断言订阅、分类、通知配置、同步记录的数量和关键字段都一致。在文档里写清楚迁移步骤。
8. **自动备份**：确认 `services/autobackup.py` 在 SQLite 下正常工作。另外在 `data/backups/` 增加一份 SQLite 文件快照，使用 `sqlite3.Connection.backup()`（不要直接复制文件，WAL 模式下直接复制会损坏），保留最近 7 份。
9. **Docker**：新增 `docker-compose.sqlite.yml`（单个 app 服务，设置 `EASYSUB_DB=sqlite`，挂载 `app_data:/app/data`）。现有的 compose 文件**不要改**，避免影响老用户。README、DOCKERHUB.md 和 `安装部署文档.md` 把 SQLite 写成新用户的首选方案，同时附上 MySQL → SQLite 的迁移步骤。

### 测试

- `test_sqlite_setup.py`：覆盖 SQLite 的 test/save 接口、path 越界被拒绝、旧配置（不带 engine 字段）仍然按 MySQL 处理、`EASYSUB_DB=sqlite` 自动初始化，以及重复启动的幂等性。
- `test_sqlite_migrate.py`：先用缺少若干列的旧表结构建一个 SQLite 库，执行 `run_migrations` 后检查列已补齐，再执行一次不报错。
- 外键：在 SQLite 下删除一条有提醒记录的订阅，应该成功。
- 用 SQLite 跑一遍完整的后端测试套件。如果 conftest 或 fixture 里写死了 MySQL，就参数化处理；`test_sync_mysql.py` 保持原样。

阶段 2 完成后提交 commit，然后直接进入阶段 3。

---

## 阶段 3：Linux 一键部署（Rust 安装器 + 内置 Python）（v2.1.0）

### 已定方案

用户已经确认：**不用 Rust 重写后端**。用 Rust 编写一个单文件程序 `easysub`，里面内置 Python 运行时、后端和前端构建产物，负责安装、启动、升级和卸载，默认使用 SQLite。业务代码只维护一份。

### 产物与目录

- 新增 Rust crate `deploy/easysub-cli/`（edition 2021）。依赖**只能使用** `clap`（derive）、`tar`、`flate2`、`sha2`、`anyhow`、`getrandom`、`hex`，dev 依赖只能用 `tempfile`。这些依赖都已经在本机 cargo 缓存中，并且已验证在 Windows 和 `x86_64-unknown-linux-musl` 上都能 `cargo check`。**不要引入** zstd、ureq、ring、openssl 或其他需要 C 编译器的 crate，因为本机无法交叉编译它们。编译一律加 `--offline`。
- payload 为 `payload.tar.gz`（用 flate2 解压），内容如下：
  - `python/`：[python-build-standalone](https://github.com/astral-sh/python-build-standalone) 的 CPython 3.12 `install_only` 包，下载时固定版本并校验 sha256；
  - `python/` 内部已经安装好 `requirements.txt` 中的所有依赖；
  - `app/`：后端代码；
  - `frontend_dist/`：前端构建产物；
  - `VERSION`。
- 构建时通过 `include_bytes!(env!("EASYSUB_PAYLOAD"))` 把 payload 嵌入二进制。目标平台为 `x86_64-unknown-linux-musl` 和 `aarch64-unknown-linux-musl`，Rust 程序本身静态链接。内置的 Python 是 gnu 版本，因此**要求 glibc ≥ 2.17，不支持 Alpine**，这一点要写进文档。
- 安装后的目录结构：

```
/opt/easysub/releases/<version>/{python,app,frontend_dist}
/opt/easysub/current -> releases/<version>
/var/lib/easysub/            # 数据目录（db、图标、备份），升级时不动
/etc/easysub/easysub.env     # JWT_SECRET（首次安装随机生成）、EASYSUB_DB=sqlite、TZ、端口
/etc/systemd/system/easysub.service
```

- **路径问题**：后端的 `data/` 和 `frontend_dist` 都是**相对于当前工作目录**的路径（`main.py:121-125`、`bootstrap.py:12`、`icons.py:19-25`、`sync.py:31`）。不要为此改后端代码。在每个 release 目录下创建软链接 `data -> /var/lib/easysub`，并把 systemd 的 `WorkingDirectory` 设为 `/opt/easysub/current`。需要用一个测试确认：`icons.py` 和 `sync.py` 中 realpath / resolve 的越界校验，在 data 是软链接时依然能放行正常文件、拦截越界路径。

### 子命令

| 命令 | 行为 |
|---|---|
| `easysub install [--port 8000] [--bind 0.0.0.0] [--data /var/lib/easysub]` | 需要 root。创建系统用户 `easysub`，解压 payload，生成 env 和 systemd unit，执行 `enable --now`，轮询 `/api/health` 最多 60 秒，成功后打印访问地址和初始管理员说明。重复执行时检测到已安装就提示改用 upgrade |
| `easysub upgrade --from-file <新二进制>` | Rust 程序**不负责联网下载**。下载和 SHA256 校验由 `install.sh --upgrade` 用 curl 完成，然后调用这条命令。处理流程：从新二进制中读取 payload，解压到新的 release 目录 → 停止服务 → 切换软链接 → 启动 → 健康检查；**健康检查失败时自动切回旧的软链接并重启**。保留最近 2 个 release |
| `easysub uninstall [--purge]` | 停止服务，删除 unit 和 `/opt/easysub`。只有加了 `--purge` 才删除数据目录和 env，删除前打印将要删除的路径并要求输入 `yes` 确认 |
| `easysub run` | 在前台运行，供没有 systemd 的环境使用（也可以不用 root，此时数据目录默认是 `./easysub-data`） |
| `easysub status` / `version` | 显示服务状态、当前版本、数据目录位置和数据库类型 |

systemd unit 的要求：`User=easysub`、`NoNewPrivileges=yes`、`ProtectSystem=strict`、`ReadWritePaths=/var/lib/easysub`、`PrivateTmp=yes`、`Restart=on-failure`。`ExecStart` 为 `/opt/easysub/current/python/bin/python3 -m uvicorn app.main:app --host ${BIND} --port ${PORT}`，并设置 `Environment=PYTHONPATH=/opt/easysub/current/app`（具体按 payload 的实际布局调整，但必须是单 worker）。

### 一键安装脚本

新增 `deploy/install.sh`，随 Release 一起发布。用法是 `curl -fsSL https://github.com/suyijun8182/easysub/releases/latest/download/install.sh | sudo bash`。脚本根据 `uname -m` 选择对应架构的二进制，下载后校验 SHA256SUMS。如果检测到已经安装，就执行 `easysub upgrade --from-file`，否则执行 `easysub install "$@"`。`/usr/local/bin/easysub` 也要更新为新版本。脚本使用 `set -euo pipefail`，下载到临时目录，退出时清理临时文件。

### CI

新增 workflow `.github/workflows/linux-binary.yml`，由现有的 tag 发布流程调用（参照 `release.yml` 使用 `workflow_call` 的方式），按矩阵分别构建 x86_64 和 aarch64：
1. 执行 `npm ci && npm run build`；
2. 下载 python-build-standalone（URL 和 sha256 固定写在 `deploy/python-version.lock`）；
3. aarch64 用 `pip install --platform manylinux2014_aarch64 --only-binary=:all: --target ...` 交叉下载 wheel。先确认 `bcrypt`、`cryptography`、`pydantic-core`、`uvloop`、`httptools`、`pillow` 都有对应的 wheel，没有的在报告里列出；
4. 打包 payload，用 `cargo zigbuild` 或 `cross` 分别编译 musl 目标；
5. **冒烟测试**：x86_64 直接运行，aarch64 用 qemu。在 `ubuntu:20.04` 和 `debian:12` 容器里执行 `easysub run`，然后 `curl /api/health`。
6. 上传 `easysub-linux-x86_64`、`easysub-linux-aarch64`、`install.sh`、`SHA256SUMS` 到对应的 Release。

### 测试

- Rust 单元测试：路径拼接与越界检查、env 生成（JWT_SECRET 长度不少于 32、重复安装不覆盖已有的 env）、unit 文本快照、升级失败回滚的状态机（文件系统操作抽象成 trait，用 mock 测试）。
- 集成测试（CI 中运行）：在 `debian:12` 容器里，用 systemd 镜像（例如 `jrei/systemd-debian`）走一遍 install → 创建订阅 → upgrade（同一版本强制升级）→ 确认数据还在 → uninstall（不加 purge）→ 确认数据目录还在。

### 文档与版本

- `APP_VERSION = "2.1.0"`。CHANGELOG 中写明新增 SQLite、新增 Linux 一键部署，以及 glibc 和架构的限制。
- 在 `安装部署文档.md` 新增“Linux 一键部署”一节，包括安装、升级、卸载、数据目录、从 Docker 或 MySQL 迁移过来的步骤。README 和 DOCKERHUB.md 同步更新。
- `GITHUB发布指南.md` 补充二进制产物的发布说明。

---

## 报告（全部做完后写一份，按阶段分节，用中文）

- 每项任务的状态和 commit hash；
- 验证命令的输出摘要（失败的要贴出原文）；
- 偏离本方案的地方及原因；
- 还没解决的问题（例如没有 aarch64 wheel 的依赖、无法覆盖的平台）；
- `git log --oneline origin/main..HEAD` 的输出。

**不要 push，不要打 tag。**
