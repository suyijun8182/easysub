# Android 0.3.0 Alpha

包名 `com.easysub.app`，versionCode 5。本次只更新 Android 客户端，服务端与网页仍为 v2.0.2。覆盖安装同签名的 0.2.0 即可保留本地资料，不要卸载或清除数据。

安装文件：`artifacts/android/EasySub-0.3.0-alpha-debug.apk`（SHA-256 见 `artifacts/android/SHA256SUMS-0.3.0`）。仍使用本机调试签名。

## 新增功能

- **到期系统通知**：续费、试用和取消截止沿用网页提醒规则，默认本地时间 09:00；普通提醒遇免打扰顺延，今天或明天到期的紧急续费可突破免打扰。点击通知进入订阅详情，开机后由插件恢复排程；普通闹钟可能有数分钟偏差，省电限制下可能更久。付款卡按 45、30、7、1、0 天提醒，与网页在 45 天内每天提醒有所不同，详见 [到期通知设计](android-native-notifications.md)。
- **应用锁（设备认证）**：冷启动和超时回到前台时需要解锁，可选择立即、1、5、15 分钟重新上锁；开启后隐藏多任务预览内容。开启和关闭均需系统认证，详见 [应用锁设计](android-native-app-lock.md)。
- **后台变更提醒**：约每 15 分钟询问服务器是否有新变更，只发送令牌、不上传业务数据；有变更时只发通知，打开 App 后才同步。可在“账号与同步”关闭，系统省电策略可能推迟检查，详见 [后台变更提醒设计](android-native-background-check.md)。
- **正式签名方案**：提供密钥保管、签名与迁移说明，目前只是文档，尚未启用。详见 [正式签名与迁移方案](android-native-signing.md)。

## 修复

- 删除确认弹窗只保留一个“取消”按钮。
- 移除“应用锁与隐私”页过时的 `preview` 删除口令说明；从 0.2.0 起使用确认弹窗加 5 秒撤销。
- 通知设置为空时，提醒页正常显示，保存其他偏好也不会覆盖原有通知设置。
- 修复原生通知插件异步加载异常，恢复权限读取与通知排程。
- 提醒内容与权限未变化时不再反复取消、重建排程。
- 系统认证超时或暂时失败时提示重试，不计入三次取消次数。
- 修复后台检查无法接受同步游标、导致快照保存失败的问题。
- 打开 App 并完成同步后，自动撤掉过时的“有新变更”通知。

## 权限变化

以下为 0.2.0 与 0.3.0 调试 APK 的 `aapt dump permissions` 实际声明对比。`android.permission.` 前缀在表中省略；声明权限不等于要求用户逐项授权。

| 权限 | 0.2.0 | 0.3.0 | 用途 |
| --- | --- | --- | --- |
| `INTERNET` | 有 | 有 | 前台同步与联网功能 |
| `VIBRATE` | 有 | 有 | 触感反馈 |
| `com.easysub.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` | 有 | 有 | AndroidX 内部广播保护 |
| `POST_NOTIFICATIONS` | 无 | 新增 | Android 13+ 由用户在提醒设置中点按钮申请，启动不自动申请 |
| `RECEIVE_BOOT_COMPLETED` | 无 | 新增 | 本地通知插件开机恢复提醒；WorkManager 恢复任务 |
| `WAKE_LOCK` | 无 | 新增 | 本地通知插件与 WorkManager 执行任务 |
| `USE_BIOMETRIC` | 无 | 新增 | 系统生物识别或设备凭据认证 |
| `USE_FINGERPRINT` | 无 | 新增 | AndroidX Biometric 的旧版指纹兼容声明 |
| `ACCESS_NETWORK_STATE` | 无 | 新增 | WorkManager 检查联网约束 |
| `FOREGROUND_SERVICE` | 无 | 新增 | WorkManager 依赖声明；本功能使用周期任务 |

没有移除旧权限；两个 APK 均无 `SCHEDULE_EXACT_ALARM`、`USE_EXACT_ALARM`。0.3.0 合并 manifest 中，插件的 `LocalNotificationRestoreReceiver` 监听 `LOCKED_BOOT_COMPLETED`、`BOOT_COMPLETED`、`QUICKBOOT_POWERON`；WorkManager 的 `RescheduleReceiver` 也声明 `BOOT_COMPLETED`（manifest 默认禁用，由库按需管理）。没有另加一套通知恢复接收器。

## 覆盖升级验收

OPPO PFVM10 / Android 12（API 31）从 versionCode 4 覆盖安装到 5 成功，未卸载、未清数据。版本由 `dumpsys package` 确认为 `0.3.0-alpha`；关于页尚不显示版本号。

升级前后均为 32 条订阅，应用锁关闭、重新上锁时间 1 分钟、后台检查开启、通知已允许；同步 cursor 均为 220，升级后成功同步时间已更新，待传与冲突均为 0。`dumpsys alarm` 中仍有 34 条提醒闹钟，`dumpsys jobscheduler` 中仍有 EasySub 的 WorkManager 作业（jobId 9）；WorkManager 数据库确认后台检查周期为 900,000 毫秒。

Codex 在本轮升级验证中未创建或修改测试订阅，未修改系统时间、通知权限、系统锁屏或触感开关；USB 保持唤醒仍为原值 0。2.7 的用户确认结果见下节。

## 人工确认（用户反馈）

- **4.0.3 振动：通过。** 用户对完整检查项回复“是”：续费全部成功与删除确认时有振动，关闭触感反馈后无振动，并按清单清理测试订阅、恢复触感开关。此结论来自用户体感确认，Codex 未代做判断。
- **网页端测试记录：已清理。** 用户确认 `DEVICE_TEST_SYNC`（id 1038，曾改名为 WEB）已在网页端手动删除；Codex 未再次操作网页数据。
- **系统锁屏 PIN：仍未删除。** 用户已确认当前状态，清理项尚未完成；是否删除由用户自行决定，Codex 未修改系统锁屏设置。

## 验收截图索引

截图保存在本地，未提交：`artifacts/android/qa-0.3.0/`。浏览器预览与真机证据分别注明；开启应用锁时禁止截图，多任务预览保护由此前真机人工确认。

| 文件名 | 说明 |
| --- | --- |
| `4.0.1-android-delete-after.png` | 浏览器 Android 预览：删除确认只剩一个取消按钮 |
| `4.0.1-web-delete-before.png` | 网页端 1280px：修复前的删除弹窗 |
| `4.0.1-web-delete-after.png` | 网页端 1280px：修复后外观保持一致 |
| `4.0.2-privacy-after.png` | 浏览器预览：移除过时口令文案 |
| `4.1-reminders-preview-zh.png` | 中文提醒设置浏览器预览 |
| `4.1-reminders-preview-en.png` | 英文提醒设置浏览器预览 |
| `4.1-reminders-preview-ru.png` | 俄文提醒设置浏览器预览 |
| `4.1-null-settings-before.png` | 浏览器：空通知设置修复前的空白页 |
| `4.1-null-settings-after.png` | 浏览器：空通知设置修复后正常显示 |
| `4.1-device-null-fixed.png` | 真机：空免打扰字段与正常权限状态 |
| `4.1-notification-shown.png` | 真机：测试到期通知出现在通知栏 |
| `4.1-notification-click-detail.png` | 真机：点击通知进入测试订阅详情 |
| `4.1-reboot-before-app.png` | 真机：重启后尚未打开 App；恢复证据另见本地闹钟日志 |
| `4.1-permission-denied.png` | 真机：系统通知关闭后的状态 |
| `4.1-permission-restored.png` | 真机：恢复通知权限后的状态 |
| `4.3-lock-preview-zh.png` | 中文锁屏浏览器预览 |
| `4.3-lock-preview-en.png` | 英文锁屏浏览器预览 |
| `4.3-lock-preview-ru.png` | 俄文锁屏浏览器预览 |
| `4.3-settings-preview-zh.png` | 中文应用锁设置浏览器预览 |
| `4.3-settings-preview-en.png` | 英文应用锁设置浏览器预览 |
| `4.3-settings-preview-ru.png` | 俄文应用锁设置浏览器预览 |
| `4.3-privacy-unavailable.png` | 真机：未设置系统锁屏时不可启用应用锁 |
| `4.3-privacy-disabled-after.png` | 真机：认证后关闭应用锁 |
| `4.5-upgrade-overview.png` | 真机：覆盖升级后总览，32 条生效订阅 |
| `4.5-upgrade-about.png` | 真机：覆盖升级后关于页；版本另由系统包信息核对 |

## 已知缺口

- Android 13 及以上的首次通知授权弹窗尚未真机验收；当前验收手机为 Android 12、API 31。本机已验证系统通知总开关的禁用及恢复路径。第 4.5 节保留此缺口，不将其记为已测。
- 应用锁冷启动锁屏页使用 App 默认语言，而不是用户保存的语言偏好：偏好保存在加密资料中，解锁前不读取。中文用户无影响。
- 应用锁真机验收只在 OPPO / Android 12（PIN，无指纹）上完成；指纹路径、Android 13+ 与其他厂商的认证框行为未覆盖。OPPO 认证框无人应答时返回错误码 2（非标准超时码 3），App 已按可重试处理。
- `AppLockStatusTest`（androidTest）未执行：`connectedAndroidTest` 结束会卸载 App；`status()` 已在真机上直接调用核对。
- 后台变更提醒只在 OPPO / Android 12 上用调试入口按需触发验证；真实 15 分钟周期在 Doze 与厂商省电策略下的实际间隔未测量，可能明显推迟。
- 后台检查的令牌刷新与"登录失效即停止"路径只有 JVM 测试，真机未制造过期令牌。
- 同步刚上传、尚未完成第二次拉取时若 App 被杀，下一次后台检查可能把本机自己的改动提示一次（只多一条通知，不影响数据）。
- 仍为调试签名；将来换正式签名时，须先按 [签名文档](android-native-signing.md) 导出并核验加密完整备份，再重装、导入，不能直接覆盖不同签名的安装包。
- 验收时临时设置的系统锁屏 PIN 仍未删除（用户已确认）；由用户自行决定是否清理，不将其记为已恢复。
