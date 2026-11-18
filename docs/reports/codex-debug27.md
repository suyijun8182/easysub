# debug27 执行报告

执行日期：2026-11-18。工作目录：`D:/Claude/easysub-debug27`，分支：`feat/debug27`。

三阶段已按顺序实施，本地可执行验证已完成。**尚未达到方案要求的完整交付状态：三个阶段均未能提交 commit，Linux CI 与 Chrome 手工验证未执行。** 没有 push、tag、Release、远端评论，也没有修改 `D:/Claude/easysub` 中的应用代码、依赖或 Git 结构。该目录下的既有 Python 环境仅用于运行测试。

## 阶段 1：续费锚定日与时区修复

| 任务 | 状态 |
|---|---|
| 审查两个测试草稿及已有 billing.py、billing-date.js 改动 | 已完成；保留核心实现和断言，调整测试组织 |
| 模型、三个 Schema、迁移列、同步字段放行 | 已实现 |
| 创建、编辑、today/due 续费、切换 day/week 的锚定规则 | 已实现并测试 |
| CSV、个人备份往返和整站恢复 | 已实现并测试；显式 NULL 保留，旧备份按创建规则补值 |
| 旧 Android 客户端不带字段时保留服务端锚定日 | 已实现并测试 |
| 网页默认日期、自动推算、续费预览使用共用日历模块 | 已实现；生产构建通过 |
| Android 离线续费、完整表单编辑和 CSV 往返 | 已实现并测试 |
| 批量续费 | 已核查；逐条调用同一续费接口，无额外日期算法 |
| 月末、闰年、旧 NULL、备注编辑、改续费日回归 | 已覆盖 |
| 洛杉矶与上海日期测试 | 已通过；冻结在上海凌晨，覆盖本地日期与 UTC 日期不同的边界 |
| Chrome Sensors 手工续费验证 | 未执行，浏览器控制通道不可用 |
| CHANGELOG、README、DOCKERHUB 顶部说明 | 已更新；已提示漂移的订阅须手动修正一次 |
| 阶段 commit | **阻塞，无 hash** |

草稿审查发现：后端测试继承 `SyncTests` 导致继承测试及导入类被重复收集；现改为复用测试夹具方法。旧同步客户端用例原先取到了续费前的同步版本，先发生冲突而没有测到目标行为，已改取最后一个版本。前端草稿仅按实际当前时间检查 todayYMD，可能漏掉 UTC 日期边界，已加入冻结时钟的断言。

阶段 1 的后端验证结果为 `75 passed, 27 skipped`；前端当时 `110 passed`，随后补齐离线编辑和 CSV 回归，最终为 `112 passed`。初始回归测试先失败，确认修复目标存在。

## 阶段 2：SQLite

| 任务 | 状态 |
|---|---|
| engine/path 配置，旧配置默认 MySQL | 已实现并测试 |
| data 内路径校验：realpath/commonpath、绝对路径、..、盘符、相邻目录 | 已实现并测试；真实符号链接测试在 Windows 跳过 |
| SQLite test/save 接口与 discriminated union | 已实现并测试 |
| WAL、foreign_keys、30 秒 timeout/busy_timeout、synchronous=NORMAL | 已实现并测试 |
| 跨方言补列与幂等迁移 | 已实现并测试；MySQL LONGTEXT 修正仍仅限 MySQL |
| SQLite 默认安装向导、MySQL 表单、三个语言文件同步 | 已实现，i18n 检查通过 |
| EASYSUB_DB=sqlite 自动配置、重复启动及保留旧 MySQL 配置 | 已实现并测试 |
| MySQL 形态备份导入新 SQLite | 已通过；校验订阅、分类、通知配置和重新生成的同步记录 |
| 开启 SQLite 外键后的带提醒订阅删除 | 已通过 |
| 加密 JSON 自动备份和 SQLite 在线快照 | 已通过；使用 Connection.backup，保留最近 7 份快照 |
| 独立 docker-compose.sqlite.yml | 已新增，原 compose 文件未修改 |
| README、DOCKERHUB、安装部署文档与迁移步骤 | 已更新 |
| 阶段 commit | **阻塞，无 hash** |

使用脱敏的 `backend/tests/fixtures/mysql-backup-debug27.json`。现有完整备份协议不导出同步日志或游标，因此恢复后生成新同步记录，测试校验 4 条记录（订阅、分类、偏好、通知配置）及锚定日内容，不伪造对旧同步 ID/游标的保留。

自动备份沿用至少 12 位 BACKUP_PASSWORD 的启用条件；启用后额外生成 SQLite 明文数据库快照，文件权限为 0600，Linux 安装器的数据目录权限为 0700。文档已说明快照包含敏感信息且不替代完整备份与图标文件保存。

阶段 2 结束时后端为 `81 passed, 28 skipped`。后续新增完整备份往返、自动备份、部署索引及路径测试，最终结果见下表。

## 阶段 3：Linux 安装器与 v2.1.0

| 任务 | 状态 |
|---|---|
| Rust edition 2021 crate、限定依赖和 Cargo.lock | 已完成 |
| 内嵌 payload、tar.gz 安全解包与二进制 payload 索引 | 已实现并测试 |
| install、run、upgrade、uninstall、status、version | 已实现；实际 Linux 运行未在本机执行 |
| root 校验、系统用户、随机 JWT、保留 env、专用数据目录 | 已实现；Linux 专用命令通过 Host trait 模拟测试 |
| release/data 软链接与 systemd 工作目录、安全配置 | 已实现；unit 文本快照测试通过 |
| 升级失败自动切回旧版本并重启、保留两个 release | 已实现；回滚状态机测试通过，真实 systemd 未执行 |
| purge 打印删除路径并要求 yes | 已实现 |
| install.sh 架构选择、固定 release 下载、SHA256、临时文件清理、更新维护命令 | 已实现；Bash 语法通过 |
| 固定 CPython 3.12.16 URL/SHA256 | 已写入 python-version.lock；仅查询元数据，未下载运行时 |
| aarch64 原生 wheel 元数据 | 六项均找到 manylinux2014 wheel，见下文；完整依赖安装仅留在 CI |
| 双架构 musl 构建、双发行版/QEMU 冒烟、systemd 生命周期 CI | 已编写并接入现有 release.yml；**未执行 CI** |
| data 软链接下 icons/sync 正常文件与越界测试 | 已新增，Windows 因无符号链接权限跳过；systemd CI 将执行 |
| APP_VERSION 2.1.0 与部署/发布文档 | 已完成 |
| 阶段 commit | **阻塞，无 hash** |

升级读取新二进制末尾 64 字节的偏移、长度、SHA256 与标记，再从原内嵌区域提取 payload；不执行新二进制，也不重复附带一份 payload。索引由 CI 的 `deploy/index_payload.py` 生成。普通本地构建使用空 payload，只用于测试，不可当作发布安装包。

本机目标已安装，`rustup target add x86_64-unknown-linux-musl` 返回 `component rust-std for target x86_64-unknown-linux-musl is up to date`。没有下载或打包 python-build-standalone。

## 最终验证摘要

| 命令/检查 | 最终结果 |
|---|---|
| backend：D:/Claude/easysub/backend/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider | **86 passed, 29 skipped, 11 warnings, 16 subtests passed in 24.07s** |
| npm run i18n:check | 三种语言、1500 条词条，全部通过 |
| npm run test:android-preview | **112 passed, 0 failed**，含日期和离线 CSV 用例 |
| node --test src/billing-date.test.js | 两个时区通过；最终也包含在上行测试脚本中 |
| EASYSUB_SYNC_FIXTURE=1 npm run test:sync | **20 passed, 0 skipped**，包含真实 FastAPI HTTP |
| npm run build -- --configLoader native | 临时副本构建通过，138 modules，2.43s；源码与已有依赖来自当前 worktree |
| cargo test --offline --locked | **7 passed, 0 failed** |
| cargo check --offline --locked --target x86_64-unknown-linux-musl | 通过，无编译警告；cargo 提示无法 canonicalize D:\Claude，但命令成功 |
| rustfmt --edition 2021 | 通过 |
| bash -n deploy/install.sh、smoke.sh、systemd.sh | 全部通过 |
| YAML 解析、部署 Python 脚本 AST 解析 | 通过 |
| git diff --check | 通过 |
| shellcheck / actionlint | 未安装，未执行 |
| Chrome Sensors、Linux 容器、systemd、aarch64 实际运行、完整发布 payload 构建 | **未执行** |

29 个后端跳过项由原有 27 个 MySQL 专项测试和两个 Windows 符号链接测试组成。没有修改 `test_sync_mysql.py`。11 个警告涉及既有依赖弃用、utcnow 和测试用短 JWT 密钥，没有后端测试失败。

前端测试使用 `NODE_OPTIONS='--preserve-symlinks --preserve-symlinks-main'` 避免 Node 在受限父目录进行 realpath。默认 esbuild 配置加载仍受权限影响，故将当前 frontend（含已有 node_modules）复制到临时测试目录，使用 Vite native 配置加载器完成构建。没有执行 npm install/npm ci 或 pip install；CI 中的安装步骤仅写入工作流，未在本机执行。

## 失败输出与处理

以下保留失败的关键原文；预期的红灯测试及开发中发现的问题均已修复，环境阻塞仍存在。

三个阶段的 git add/commit 都失败：

```text
fatal: Unable to create 'D:/Claude/easysub/.git/worktrees/easysub-debug27/index.lock': Permission denied
```

Git 元数据位于只读的主仓库目录，而当前权限策略不允许提权。没有改写 .git 文件、另建仓库替换当前 worktree、修改主仓库权限或伪造提交。因此三个阶段均没有 commit hash，工作保留为未提交改动。

默认 Node 与构建失败原文：

```text
Error: EPERM: operation not permitted, lstat 'D:\Claude'
✘ [ERROR] Cannot read directory "../..": Access is denied.
✘ [ERROR] Could not resolve "D:\\Claude\\easysub-debug27\\frontend\\vite.config.js"
```

尝试 `--configLoader runner` 仍因 `lstat 'D:\Claude'` 失败；临时目录的默认 esbuild loader 也失败：

```text
✘ [ERROR] Cannot read directory "../../../..": Access is denied.
```

临时副本首次拷贝错误地忽略了依赖包内部 dist，导致以下错误；修正复制规则后使用 native loader 构建通过，未修改任何依赖内容：

```text
Error [ERR_MODULE_NOT_FOUND]: Cannot find module 'C:\Users\AidenSu\AppData\Local\Temp\easysub-debug27-build\node_modules\@intlify\message-compiler\dist\message-compiler.mjs'
```

浏览器失败原文：

```text
Computer Use native pipe is unavailable: failed to connect native pipe: 系统找不到指定的文件。 (os error 2)
```

初始阶段 1 红灯摘录：

```text
E KeyError: 'billing_anchor_day'
E AssertionError: '2027-03-28' != '2027-03-31'
3 failed, 26 passed, 4 warnings in 9.85s
```

修正草稿测试组织并补充测试后，目标红灯为 `5 failed, 2 passed`；实现后全部通过。初始同步草稿误取旧版本还产生过 `E AssertionError: 'conflict' != 'applied'`，已修正测试，不通过绕开冲突机制实现。

阶段 2 初始红灯摘录：

```text
E AssertionError: False is not true
E KeyError: 'user'
E AssertionError: 422 != 200
E AssertionError: 'billing_anchor_day' not found in {'name', 'id'}
4 failed, 1 skipped, 2 warnings in 1.56s
```

开发中修复的失败摘录：

```text
PermissionError: [WinError 32]
E AssertionError: 4 != 2
error[E0599]: no method named `header_mut` found for struct `tar::Entry<'a, R>`
AssertionError [ERR_ASSERTION]: The expression evaluated to a falsy value:
  assert.ok(content.includes('billing_anchor_day'))
```

分别修复为：显式关闭 SQLite 快照连接再原子替换文件；同步记录断言计入偏好与通知配置；使用 tar 的 set_mask；离线 CSV 加入锚定日列。最终对应测试均通过。

格式化命令带 offline 参数不被 cargo-fmt 接受，改用独立 rustfmt：

```text
error: unexpected argument '--offline' found
Usage: cargo fmt [OPTIONS] [-- <rustfmt_options>...]
```

曾从 backend 跨目录收集部署 Python 测试，pytest 探测父目录失败，已将该测试放入 backend/tests：

```text
E PermissionError: [WinError 5] ... 'D:\\Claude'
ERROR .. - PermissionError: [WinError 5] ... 'D:\\Claude'
1 warning, 1 error in 0.29s
```

真实 HTTP fixture 启动时既有 passlib 打印以下兼容性提示，但服务启动且 20 项 HTTP/同步测试通过；测试结束后已停止该临时服务：

```text
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

## 平台与依赖限制、方案偏离

- 三个阶段无法提交是主要未完成项；不会提供不存在的 hash。
- Chrome 手工 UI、Linux 安装/升级/卸载实际运行、容器与 systemd CI 均未执行。不能据本地单元测试声称这些已通过。
- 本地只检查了 x86_64 musl 编译；aarch64 构建和 QEMU 运行留在 CI。
- 使用临时副本和 native loader 构建前端，保留默认构建的失败记录；没有为沙箱问题修改项目构建配置。
- 未新增 MySQL 数据迁移工具，复用完整备份；同步记录重新生成，旧游标不保留。
- 系统集成镜像由 debian:12 自建，避免依赖第三方 systemd 镜像的可用 tag；验证流程仍按方案执行。
- 为满足“cargo 全部 offline”，CI 使用 Cargo.lock 的 checksum 下载 vendor 内容，再运行 cargo test/cargo zigbuild --offline；没有添加额外 crate 依赖。
- 既有 .gitignore 忽略了安装部署文档和 GitHub 发布指南；现解除这两项忽略，使要求的指南更新能纳入后续提交。
- 原先未提交的 docs/plans 与 frontend/.npm-cache 未删除。构建产物、target、临时依赖副本未纳入源文件。

查询 PyPI 官方元数据，以下六项存在 CPython 3.12 可用的 aarch64 manylinux2014 wheel，未发现这六项缺失：

| 依赖 | 已核对版本 | 官方元数据 |
|---|---|---|
| bcrypt | 4.2.1 | https://pypi.org/pypi/bcrypt/4.2.1/json |
| cryptography | 50.0.2 | https://pypi.org/pypi/cryptography/50.0.2/json |
| pydantic-core | 2.27.2 | https://pypi.org/pypi/pydantic-core/2.27.2/json |
| uvloop | 0.21.0 | https://pypi.org/pypi/uvloop/0.21.0/json |
| httptools | 0.6.4 | https://pypi.org/pypi/httptools/0.6.4/json |
| pillow | 12.2.0 | https://pypi.org/pypi/pillow/12.2.0/json |

Python URL 与 SHA256 取自 https://api.github.com/repos/astral-sh/python-build-standalone/releases/tags/20261110 的官方资产元数据。**未实际下载/安装整个目标依赖集合，最终 wheel 解析、运行时 ABI 和 glibc 基线仍需 CI 验证。**

## Git 日志

执行：

```text
git log --oneline origin/main..HEAD
```

实际输出为空，没有新增提交；当前分支仍为 `feat/debug27`。
