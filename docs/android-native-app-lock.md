# Android 应用锁设计

日期：2026-11-16。状态：实现方案，真机验收结果另记。

## 认证与存储边界

应用锁使用系统设备认证，不增加网站口令，也不修改或重置业务数据。信任边界在 Java 插件调用系统 BiometricPrompt；JS 只控制显示和启动顺序，不能自行将认证结果当作系统认证。设置仅保存 enabled 和 relockMinutes 到独立 SharedPreferences，不保存生物信息或设备密码。

使用稳定版 `androidx.biometric:biometric:1.1.0`，版本变量放在 variables.gradle。认证组合为 `BIOMETRIC_WEAK | DEVICE_CREDENTIAL`，不使用旧系统不支持的 `BIOMETRIC_STRONG | DEVICE_CREDENTIAL`。status 同时检查系统锁屏是否安全及 canAuthenticate；无设备密码时不可启用。

来源：[AndroidX 发布页](https://developer.android.com/jetpack/androidx/releases/biometric)、[Android 认证说明](https://developer.android.com/identity/sign-in/biometric-auth)。

## Java 插件

AppLockPlugin 在 MainActivity 注册。status 返回 enabled、available、reason、relockMinutes；reason 为可翻译的原因代码。authenticate 在主线程显示 BiometricPrompt，成功 resolve，取消映射 CANCELED，锁定映射 LOCKOUT，其余不可用错误映射 UNAVAILABLE。指纹未匹配由系统提示继续尝试，只有系统终止认证才结束调用；不记录认证信息。

setEnabled 的开启、关闭和超时变更均先完成系统认证再写设置；只接受立即、1、5、15 分钟，默认 1。认证取消或错误时设置保持原值，不提供跳过认证或强制关闭的调试入口。并发认证拒绝，避免多个调用共用回调。

MainActivity 在创建 WebView 之前读取开关，开启时设置 FLAG_SECURE；设置变更成功后即时更新窗口标记。该标记阻止截图并隐藏多任务预览内容。认证开启期间不为了获取截图临时移除保护。

## 冷启动与前后台

在调用 openStorage / createLocal 之前初始化独立锁屏视图并等待系统认证成功。锁屏不读取订阅、金额、账号或通知密钥，只显示当前语言的状态及动作。status 调用失败时保持遮罩，不继续加载本地资料。

前后台由纯 JS 控制器记录离开时间。离开时立即遮蔽业务 DOM；超时前返回可直接恢复，达到超时则保持遮罩并认证。立即模式每次离开后返回均认证。同步、在线恢复、定时同步及通知点击跳转均等待可访问状态，取消认证不能启动这些动作。窗口 FLAG_SECURE 提供原生截图保护，JS 遮罩同时禁止底层焦点和交互。

认证取消保留“解锁”和“退出”；连续取消 3 次后只保留退出，退出调用 App.exitApp，重新启动才可再次尝试。锁定或取消永远不删除或重置数据。已开启时若系统设备锁被移除，保持应用锁开启，显示恢复设备锁的原因，只提供退出；不静默关闭。

## 设置与语言

“应用锁与隐私”替换过时说明，提供开关、重新上锁时间及当前状态。开启、关闭及时间修改均显示系统认证；界面只在原生成功后更新。浏览器预览显示无法执行设备认证并禁用操作，不模拟开启成功。所有可见状态、按钮和认证理由提供中、英、俄三语；冷启动语言使用可用的界面偏好，不为读取语言而提前解密资料。

## 验证

纯 JS 先写失败测试，覆盖冷启动的数据加载门禁、前台超时与未超时、立即模式、取消次数、设备不可用、认证失败及同步等待。JVM 单测覆盖时间选项和错误映射；androidTest 验证 status 在本机返回合理值。

运行前端检查、APK 构建及 JVM 单测。真机由用户完成系统认证，验证开启与关闭、冷启动先解锁、后台超时、未超时、连续取消及再次打开数据保留、多任务保护。FLAG_SECURE 开启时截图不可用的项保持“未验收”直到用户实际确认，再写“人工看过”；不把黑截图当作保护效果的充分证明。

Android 13+ 通知首次授权弹窗的缺口已单独记录到 android-0.3.0.md，留到 4.5 汇总。
