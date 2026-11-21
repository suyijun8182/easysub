# Android 0.3.2 Alpha

包名 `com.easysub.app`，versionCode 7。本次只更新 Android 客户端，服务端与网页仍为 v2.1.0。覆盖安装同签名的 0.3.x 即可保留本地资料，不要卸载或清除数据。

安装文件：GitHub Release `android-v0.3.2-alpha` 中的 `EasySub-0.3.2-alpha-debug.apk`（SHA-256 见同页 `SHA256SUMS-0.3.2`）。仍使用本机调试签名。权限与 0.3.0 相同。

0.3.1 的汇率改动见 [Android 0.3.1](android-0.3.1.md)；功能、权限与签名说明见 [Android 0.3.0](android-0.3.0.md)。

## 修复：顶栏被状态栏遮挡

用户反馈：App 顶部的 EasySub 标志和右上角的同步按钮被时间、信号、电量图标盖住，同步按钮很难找到。

- **原因**：Capacitor 8 让页面延伸到状态栏下面。手机上的 Android System WebView 为 140 及以上时，系统不再为页面让出状态栏，需要网页自己避开；低于 140 时由系统在页面外留出空间。所以只有部分手机出现这个问题。
- **修复**：首页顶栏、设置子页返回栏、全屏弹窗、普通弹窗和应用锁屏都会按状态栏高度下移。优先使用 Capacitor 注入的 `--safe-area-inset-*`，读不到时再用 `env(safe-area-inset-*)`。旧版 WebView 读到的值是 0，界面不变。
- **底部**：底部导航、多选操作栏和底部弹层也改用同一套数值，旧版 WebView 上不会再把手势条区域算成 0。

## 已验证

- `test:android-preview`（112 通过）、Android 网页构建通过。
- `build-apk.ps1` 构建成功，JVM 单元测试通过；`aapt dump badging` 确认 `versionCode='7' versionName='0.3.2-alpha'`。
- 真机（WebView 140 及以上）覆盖升级：未验收。
