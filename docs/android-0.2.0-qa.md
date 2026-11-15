# Android 0.2.0 验收记录

证据目录：`artifacts/android/qa-0.2.0/`（本地产物，不进入 Git）。所有浏览器写操作仅使用 `android-features.html` 的 `seed.json` 内存演示数据。

## 阶段 0

- `99817ff` cherry-pick 为 `eaa35f0`；唯一冲突保留 origin 的 versionCode 3 / 0.1.3-alpha。
- i18n 检查通过；Android 预览测试 28/28；网页、预览和 APK 构建通过（Gradle 41s）；生产依赖审计 0 漏洞。
- `0-web-{dashboard,subscriptions,settings}-{before,after}-light-zh.png`：1280px 宽、相同演示 API、等待字体和动效稳定后三组截图逐字节相同，比较明细 `0-web-compare.json`。

## 1.1 收起卡片

- `1.1-stack-light-zh.png`；隐藏卡背的子元素 `visibility:hidden`，底层卡片均 `inert`，第四张起 `display:none`。
- `stack-accessibility.test.js` 直接渲染实际卡片模板，覆盖收起、展开和保存中的焦点约束。已有行为正确，本项补充测试及截图，没有改动行为。

## 1.2 按钮完整换行

- `1.2-subscriptions-light-zh.png`，明细 `1.2-buttons.json`；所有“编辑订阅”按钮均 `white-space:nowrap`，内容宽度未超出按钮，按钮边框盒高度保持 48px。
- debug23 已有 `.sc-acts { flex-wrap:wrap }` 和按钮 `flex:1 1 max-content`，本项复核通过，无需重复修改样式。
- 浏览器视口 360×800、DPR 2；用各元素字号乘 1.35 近似 Android WebView textZoom，保留 CSS 尺寸。Chrome 的 OS 字号仿真只暴露系统文字比例，不能单独代表 WebView 的放大效果。此为浏览器预览证据，尚未完成真机对应截图复核。

没有向真实账号提交续费、修改或删除订阅；没有修改手机设置。
