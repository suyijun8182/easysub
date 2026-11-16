# Android 正式签名与迁移方案

日期：2026-11-16。状态：提案，待用户审阅。本项只交付文档；以下命令和配置均未执行或应用，不生成密钥，不改 CI。

## 现状与适用范围

当前包名为 `com.easysub.app`。`frontend/scripts/build-apk.ps1` 调用 `assembleDebug testDebugUnitTest`，APK 使用本机 Android 调试签名；`frontend/android/app/build.gradle` 尚未配置 `signingConfigs.release`。当前构建不会产出正式签名包。

现有调试版不能直接覆盖安装使用另一把正式密钥签名的 APK，Android 会拒绝签名不匹配的更新。此次方案不使用签名轮换，也不把调试密钥继续用作发布密钥。迁移步骤见下文；本次 0.3.0 的真机覆盖安装仍使用原调试签名，不执行卸载迁移。签名与更新要求参见 [Android 官方签名说明](https://developer.android.com/studio/publish/app-signing)。

APK 签名密钥用于证明安装包来源；手机 Android Keystore 中的 `easysub.local.v1` 用于加密本地资料，两者用途不同。不能用 APK keystore 解密 `local-v1.enc`，也不能靠复制该文件完成卸载后的恢复。

## 密钥生成与保管

用户决定分发渠道后，在可信离线电脑使用 JDK 21 的 `keytool` 生成密钥。以下 PowerShell 示例选择 RSA 4096，证书有效期为 10000 天，超过 25 年；路径位于仓库之外，父目录由用户事先准备。命令省略密码参数，由工具交互询问，避免密码进入命令历史。证书身份字段由用户填写；证书会随 APK 公开，不填写不愿公开的个人信息。

```powershell
keytool -genkeypair -v -storetype JKS -keystore 'E:/OfflineKeys/easysub-release.jks' -alias easysub-release -keyalg RSA -keysize 4096 -sigalg SHA256withRSA -validity 10000
keytool -list -v -keystore 'E:/OfflineKeys/easysub-release.jks' -alias easysub-release
```

如选择 EC，将生成命令中的 `-keyalg RSA -keysize 4096 -sigalg SHA256withRSA` 换为 `-keyalg EC -groupname secp256r1 -sigalg SHA256withECDSA`，路径和别名也改为用户选定值。两种命令只选一种，不为同一发布身份反复生成密钥。参数定义见 [JDK 21 keytool 手册](https://docs.oracle.com/en/java/javase/21/docs/specs/man/keytool.html)。

若启用 Play App Signing，另建上传密钥：以上述命令为模板，将文件名和别名分别改为 `easysub-upload.jks`、`easysub-upload`。上传密钥签署提交给 Play 的产物，最终安装到手机上的 APK 由 App 签名密钥签署；不要把上传密钥签名的 APK 当成可覆盖 Play 版本的独立安装包。

密钥和密码由用户离线保管，至少保留两处独立备份，并确认两处均可读取。分别保存 keystore、密码、别名和证书 SHA-256 指纹，不把密码写入仓库或构建日志。每次正式发布保留证书指纹记录，以便确认后续包使用相同身份。

自行分发 APK 时，发布私钥丢失且无可用备份，就无法继续向现有用户提供同包名的兼容更新。Play App Signing 的上传密钥丢失可申请重置，不能将这项恢复能力套用于自行保管的 App 签名私钥。[Android 官方文档](https://developer.android.com/studio/publish/app-signing) 说明了两种情况的区别。

## Gradle 接入方案

后续实施时，`frontend/android/app/build.gradle` 从四个环境变量读取配置：

| 环境变量 | 内容 |
| --- | --- |
| `EASYSUB_KEYSTORE_PATH` | 仓库外 keystore 的绝对路径 |
| `EASYSUB_KEYSTORE_PASSWORD` | keystore 密码 |
| `EASYSUB_KEY_ALIAS` | 私钥别名 |
| `EASYSUB_KEY_PASSWORD` | 私钥密码 |

下面是供后续合入现有文件的 Groovy 片段，不是完整替换文件。保留现有 `android` 设置及 release 混淆配置；debug 构建不需要这些变量。release 请求缺少任何变量或文件不存在时明确失败，密码错误、别名错误由 Android 签名任务报错，均不得回退到调试签名。

```groovy
// Place before the existing android block.
def releaseEnvNames = [
    'EASYSUB_KEYSTORE_PATH', 'EASYSUB_KEYSTORE_PASSWORD',
    'EASYSUB_KEY_ALIAS', 'EASYSUB_KEY_PASSWORD'
]
def releaseEnv = releaseEnvNames.collectEntries { name ->
    [(name): System.getenv(name)]
}
def missingReleaseEnv = releaseEnvNames.findAll { name ->
    releaseEnv[name] == null || releaseEnv[name].isEmpty()
}

android {
    signingConfigs {
        release {
            if (missingReleaseEnv.isEmpty()) {
                storeFile file(releaseEnv.EASYSUB_KEYSTORE_PATH)
                storePassword releaseEnv.EASYSUB_KEYSTORE_PASSWORD
                keyAlias releaseEnv.EASYSUB_KEY_ALIAS
                keyPassword releaseEnv.EASYSUB_KEY_PASSWORD
            }
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            // Keep the existing minifyEnabled and proguardFiles settings.
        }
    }
}

// Inspect resolved tasks so an aggregate `build` also validates release inputs.
gradle.taskGraph.whenReady { graph ->
    if (graph.allTasks.any { task ->
        task.project == project && task.name.toLowerCase(java.util.Locale.ROOT).contains('release')
    }) {
        if (!missingReleaseEnv.isEmpty()) {
            throw new GradleException('Release signing requires: ' + missingReleaseEnv.join(', '))
        }
        def keystore = file(releaseEnv.EASYSUB_KEYSTORE_PATH)
        if (!new File(releaseEnv.EASYSUB_KEYSTORE_PATH).isAbsolute() || !keystore.isFile()) {
            throw new GradleException('Release keystore must be an existing absolute file path')
        }
    }
}
```

片段在验证时检查原始路径，因为 `file()` 会把相对路径转为绝对路径。这里采用当前工程的普通 Gradle 任务图方式；未来若启用 configuration cache，应改成兼容该模式的验证任务。

后续验收覆盖：四项全部缺失、各缺一项、路径不存在、密码错误、别名错误均使 release 失败；没有变量时 debug 仍可构建；正确配置产出 release APK，用 SDK 的 `apksigner verify --verbose --print-certs` 核对证书指纹。此文档阶段未运行这些构建场景，不能视为签名实现已验证。

## GitHub Actions 方案

用户决定采用 CI 签名后，再单独修改工作流。keystore 转为 base64 后存入 GitHub Actions secret `EASYSUB_KEYSTORE_BASE64`，另外保存上述两个密码及别名的同名 secrets。路径由 runner 临时目录生成，不需要保存为 secret。base64 只是编码，不提供加密保护，参见 [GitHub Actions secrets 文档](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)。

签名流程只接受 tag 推送，事件过滤与签名 job 条件都限定 `refs/tags/android-v*`；网页使用的 `v*` tag、分支、PR 和手动触发均不进入签名 job，避免与网页版 Docker 发布和 Release 工作流混用。示意条件如下：

```yaml
on:
  push:
    tags: ['android-v*']

# Inside the signing job:
if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/android-v')
```

建议使用临时 Ubuntu runner，并将签名放在独立 job，避免向 PR 或不可信脚本提供 secrets。步骤顺序为：

1. 检出目标 tag，准备锁定依赖、JDK 21 和 Android SDK，完成前端构建及 `cap sync android`。
2. 用步骤级环境变量传入 secret，关闭 shell 跟踪，以 `umask 077` 限制权限；将 base64 解码到 `$RUNNER_TEMP/easysub-signing/release.jks`。不将密钥写入仓库、缓存或上传产物。
3. 在同一步骤设置四个签名环境变量，调用 `:app:assembleRelease :app:testReleaseUnitTest`；Play 渠道另用 `:app:bundleRelease` 产出上传用 AAB。
4. 校验 APK 签名及预期证书 SHA-256 指纹，为最终 APK 或 AAB 计算文件 SHA-256，生成 `SHA256SUMS`，只收集包文件、校验和及公开证书指纹。
5. 在签名 shell 中用退出 trap 删除临时 keystore，并增加 `if: always()` 的清理步骤兜底。清理路径固定在 runner 临时目录，失败时也执行；意外终止由临时 runner 销毁兜底。

若使用 Play 与独立 APK 两种渠道，分别配置 upload 与 release 密钥来源，不能让同一组 secrets 随渠道隐式切换身份。文件 SHA-256 用于核对下载内容，证书 SHA-256 用于核对签名身份，两者都要记录。

本提案不创建 tag，不改现有工作流，也不发布或上传任何产物。正式落地时需测试网页 `v*` tag 及非 tag 均无签名、缺 secret 失败、成功与失败均清理临时密钥、产物无密钥文件。

## 是否采用 Play App Signing

| 路径 | 收益 | 代价与限制 |
| --- | --- | --- |
| 自管签名，独立 APK 分发 | 用户直接控制发布私钥及 APK 分发，可离线签名 | 需长期保管及备份发布私钥，自行处理下载与升级；丢失私钥会中断兼容更新 |
| Play App Signing | Google 保管 App 签名密钥，上传密钥可重置，Play 负责签发分发包 | 需维护 Play 账号及发布流程；上传签名与安装包签名分离，跨渠道升级需事先统一签名身份 |

若希望 GitHub APK 与 Play 安装的 App 能互相更新，应在接入 Play 时选择提供自己的 App 签名密钥，并保留用于独立 APK 签名的安全备份；还要核对两个渠道的实际证书和版本号。若由 Google 生成 App 签名密钥，不能假定本地上传密钥可以签出相同身份的 APK。渠道选择由用户决定，本项不代替用户注册或配置 Play。相关机制见 [Play App Signing 官方说明](https://developer.android.com/studio/publish/app-signing#app-signing-google-play)。

## 用户迁移步骤

**卸载会删除本地数据，必须先导出备份。** 以下流程仅在用户决定从调试签名迁移至正式签名时执行；本次仅编写方案，不操作手机。

1. 在旧版 App 的设置中进入备份页，使用“完整加密导出”，设置并妥善保存备份密码。使用系统文件选择器，把文件保存到卸载后仍可访问的位置，再复制一份到电脑或其他独立存储。
2. 确认导出成功、两份文件可读取，并在保留旧版的前提下，用现有导入入口解密到恢复摘要，核对订阅等记录数量；到摘要后停止，不点“确认恢复”。若解密或数量不对，不卸载，先重新导出并核验。
3. 用户核验备份后，才卸载调试版。卸载将删除 App 私有数据和本地加密密钥；服务器同步不能代替完整本地备份。
4. 安装用户核验来源和证书指纹后的正式签名版。
5. 在新版的备份导入入口选择加密文件，输入密码，核对恢复摘要后确认导入。检查订阅、分类、付款方式、通知配置、图标、偏好、汇率和日志。现有导出属于业务数据备份，不是原始私有目录镜像，不含同步登录令牌；设备本地开关、权限及后续应用锁配置需要重新核对。
6. 若此前使用服务器同步，在“账号与同步”重新登录并确认服务器及账号，处理界面提示的首次连接差异。先完成本地恢复，再连接同步，避免把空白资料库误当成迁移完成。
7. 核对系统通知权限、提醒排程和触感反馈等设备设置；保留两份备份，直到确认迁移数据完整且后续正式版可正常更新。

迁移演练应先用隔离设备或测试安装中的 `DEVICE_TEST_` 数据验证导出、卸载、重装、导入及再次覆盖更新。真实账号的手机在用户完成备份核验并决定迁移前，不卸载、不清数据。当前计划第 4.5 节的调试版覆盖升级不采用这条卸载流程。

## 待用户决定

- 是否上 Google Play，还是只分发独立 APK；若两者都用，是否要求跨渠道覆盖升级。
- 发布密钥选择 RSA 4096 还是 EC；保管人、两处离线备份位置及恢复演练安排。
- 是否启用 Play App Signing；若启用，是否提供自有 App 签名密钥，并另建上传密钥。
- 是否让 GitHub Actions 持有签名密钥，还是在离线电脑签名后手动提供包及 SHA-256；若用 CI，由谁维护 secrets 与 tag 发布权限。
- 何时进行从调试版到正式版的卸载迁移，以及备份核验和隔离演练结果是否满足条件。

文档验收由用户审阅完成。审阅前不执行上述密钥、CI 或迁移动作；其他 0.3.0 原生功能继续按计划使用调试签名。
