# Android Alpha 0.1.0

首个独立 Android 调试安装包，包名 `com.easysub.app`，最低 Android 7，目标 Android 16。当前设备是 OPPO PFVM10 / Android 12。

安装文件：`artifacts/android/EasySub-0.1.0-alpha-debug.apk`。使用本机 Android 调试签名，不是正式发布签名，也未上传 GitHub。不要卸载以测试升级；应使用覆盖安装保留本地资料。

## 本阶段实现

- Capacitor 8.6 原生工程，界面与静态图标直接打包，启动不依赖电脑、Vite 或网站服务。
- Android Keystore AES-256-GCM 密钥、应用私有 no_backup 加密文件、AtomicFile 写入。资料、令牌、游标与待传队列同文档保存；解密失败保留原文件并停止启动，不重置为空库。
- 关闭 Android 自动备份，避免仅恢复密文却丢失设备密钥；应另行导出有密码的完整备份。
- 系统文件选择器保存加密备份及 ICS；浏览器版继续使用下载方式。导入沿用原生 WebView 文件选择器。
- Android 返回键优先关闭弹层，再返回应用内页面；无历史时回到总览，根页面返回才退出。回到前台触发可选同步。
- 沿用已审核的五项导航、主题语言、本地业务界面和服务器同步协议。关闭 Capacitor 详细桥接日志，避免保存方法的敏感参数进入调试日志。

原生存储与浏览器资料库独立，不自动迁移电脑上的浏览器数据。Alpha 删除订阅仍使用 `preview` 作为防误操作确认文字，不是网页密码或设备认证。

## 构建

在 frontend 执行 `./scripts/build-apk.ps1`。需要 Node 22+、JDK 21、Android SDK 36 和 Build Tools 36；本机工具下载在已忽略的 `.android-tools`，没有写入仓库。

脚本先构建 Vue 资源和同步 Capacitor，再将 Android 源码复制到独立 Windows 临时目录构建，最后回收 APK。临时目录构建规避当前工作盘上 Gradle 的文件快照异常；不关闭加密或降低 Android SDK 目标版本。

技术依据：[Capacitor 接入现有 Web 工程](https://capacitorjs.com/docs/getting-started)、[Android 自定义原生能力](https://capacitorjs.com/docs/android/custom-code)。本工程打包的是已有离线客户端，不是远程网页地址。

## 验证与剩余范围

Android APK 编译已成功；前端 27 项测试通过，需要独立服务的 HTTP 项本轮跳过。真机 instrumentation 测试 `NativeStorageTest.coldLaunchLoadsAndAtomicallySavesEncryptedDatabase` 已执行，结果 `OK (1 test)`，覆盖冷启动后数据库保存、加密文件封装与不保存明文业务字段。

初次 USB 安装曾因 OPPO 增强防护和设备断连失败。手机联网后完成扫描，结果“暂无风险”，已成功安装及覆盖更新，没有修改安全保护设置。Android Lint 已在临时构建目录通过。

已通过真实界面新增 `DEVICE_TEST_20261101` 订阅，强制结束进程并冷启动后确认记录仍在，再通过删除确认清理测试订阅。设备 `no_backup/local-v1.enc` 已生成。保留手机 135% 字体设置，发现并修正底栏长标签换行：采用总览/订阅/日历/报表/设置，并按实际底栏高度预留内容空间。另修正本地删除框误要求网页登录密码的文案，明确为 Alpha 确认文字。尚未执行真正断网、完整备份恢复、语言切换及全部页面验收，不能用上述结果代表完整真机验收通过。

仍待完成：系统通知、重启恢复、Android 后台同步/备份、设备认证、逐渠道真实通知发送、正式签名与升级验证，以及完整真机 UI/离线/备份恢复验收。首个 Alpha 不等于整体 App 完成。
