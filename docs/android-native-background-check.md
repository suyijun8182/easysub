# Android 后台变更提醒设计

日期：2026-11-16。状态：实现方案。对应计划 4.2（2026-11-15 用户改定）。

## 目标与边界

App 不在前台时，定期用已保存的登录凭据问一次服务器"有没有新变更"；有就发一条本地通知，提示用户打开 App。**真正的同步仍由打开 App 后的现有 JS 引擎完成**，后台不拉取、不合并、不上传任何业务数据。原因：同步引擎是 JS，WorkManager 运行时没有 WebView；用 Java 再写一份同步会出现两套实现。

## 判断"有新变更"

服务器 `GET /api/sync/v1/capabilities` 返回 `epoch` 和 `cursor`。每个账号的 `cursor` 每发生一条变更加 1（`backend/app/services/sync.py`）。后台把它与 App 最近一次完整同步后记录的 `epoch/cursor` 比较：

- `epoch` 不同（服务器资料库被恢复）或服务器 `cursor` 更大 → 有新变更；
- 否则没有。

**自己的上传不能被当作新变更。** 同步引擎先拉取再上传，上传后本地 `cursor` 不会前进。为此 `src/sync/local.js` 在本轮有上传时立即再拉取一次，把本机刚上传的变更也纳入本地 `cursor`，然后才把快照交给后台。仍有一个极小窗口：上传成功后、第二次拉取完成前 App 被杀，快照停留在旧值，下次后台检查会把这些自己的变更报告一次。只会多一条提示，不影响数据，接受。

## 数据交接（JS → 原生）

- `createLocal(..., hooks)`：`hooks.synced({ server, tokens, epoch, cursor })` 在每次完整同步成功后调用；`hooks.unlinked()` 在暂停同步、退出登录、令牌失效（401/403）、服务器重置或协议不可用时调用。同步失败（如断网）不调用，后台继续使用上一份快照。
- `EasySubDevice.setBackgroundCheck({ server, access_token, refresh_token, epoch, cursor, locale })`：写入 `noBackupFilesDir/bg-check-v1.enc`。复用本地资料库的 Keystore 密钥（`easysub.local.v1`）和同样的 AES-GCM + AtomicFile 格式，不另建密钥。
- `EasySubDevice.clearBackgroundCheck()`：删除快照并取消任务。
- 快照只含服务器地址、两个令牌、epoch、cursor、通知语言和去重标记，不含订阅等业务数据。`allowBackup="false"` 与 no_backup 目录保证它不进系统备份。

## 后台任务

- WorkManager 唯一周期任务 `easysub-background-check`，15 分钟（系统允许的最小值），约束"已联网"，`ExistingPeriodicWorkPolicy.UPDATE`，指数退避（起始 1 分钟）。
- 每次运行：读快照 → 校验地址（只允许 HTTPS，`localhost/127.0.0.1/[::1]` 可用 HTTP；不带账号、查询、锚点，与 `transport.js` 的 `serverUrl()` 一致）→ 带 access token 请求 capabilities（超时 20 秒，不跟随重定向）。
- 401：用 refresh token 调 `POST /api/auth/refresh`。服务器的 refresh 令牌是无状态 JWT，刷新不会作废旧令牌，所以后台刷新不影响 App 自己保存的令牌。新令牌**只写回后台快照**，然后重试一次。
- 刷新也返回 401/403，或 capabilities 返回 403：清除快照、取消任务，不发通知；用户打开 App 后由现有同步界面提示重新登录。
- 网络错误、超时、5xx、重定向、响应格式错误：`Result.retry()` 指数退避，不弹窗、不发错误通知。
- 有新变更且这个状态（epoch + cursor）还没通知过 → 发通知，并在快照里记下 `notified_epoch/notified_cursor`。之后服务器又有新变更会再通知一次；通知使用固定 ID 并设 `setOnlyAlertOnce`，所以不会在通知栏里堆积。
- App 完成同步后，新快照的 cursor 会达到或超过已通知值，去重标记自然失效。

## 通知

- 独立渠道 `easysub-sync-v1`（中：同步、英：Sync、俄：Синхронизация），与到期提醒分开，用户可单独关闭。
- 文案按快照里的语言（zh/en/ru），只写"网页端有新的变更，打开 App 同步"，不含订阅名称；锁屏可见性为私密。
- 点击打开 App。回到前台本来就会触发同步。若开启了应用锁，先解锁再同步。
- App 完成一次同步、交出新快照时撤掉这条通知（无论用户是点通知还是从桌面打开），避免通知栏留下过时提示。
- 没有通知权限时照常检查，但不发通知，也不记去重标记，这样授权后的下一次检查还能提醒。

## 设置

"账号与同步"页在已登录时显示"后台检查变更"开关，默认开启，保存在原生 `SharedPreferences`。关闭时取消任务（保留快照，以便重新开启后立即生效）；开启时若有快照就排程。说明文字（三语）写明：每 15 分钟一次，只发送登录凭据询问是否有变更，不上传数据；需要通知权限；系统省电策略可能推迟检查。

## 测试

- JS（`src/sync/local.test.js`）：完整同步后快照的 cursor 等于服务器 cursor（含本机上传）；失败不交快照；暂停、退出登录、401 均撤销快照。
- JVM（`BackgroundCheckTest`）：判断逻辑抽成纯 Java，HTTP 与存储用假实现。覆盖：无变更不通知；cursor 前进通知一次并去重；继续前进再通知；epoch 变化通知；401 → 刷新成功 → 重试，新令牌写回；刷新失败 → 清除并停止；5xx/网络错误 → retry；非 HTTPS/带查询的地址拒绝；无通知权限不记去重标记。
- 真机：见计划 4.2 验收步骤，只用 `DEVICE_TEST_SYNC` 测试订阅，验完删除。
