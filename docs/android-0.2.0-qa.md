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

## 1.3 主题与语言

- 共 27 张：`1.3-{overview,renewals,subscriptions,settings}-{light,dark}-{zh,en,ru}.png`，以及 `1.3-overview-{ocean,forest,purple}-zh.png`。
- 浏览器预览检查了截图；正文、辅助文字、操作文字和三种风险标签的主题变量对比度最低 4.534:1（过期红色在浅红底）。风险语义不随主题改变，明细 `1.3-matrix.json`。
- 中英俄页面可渲染，浏览器控制台没有错误。已有数字与单位换行、列表密度、付款方式双语和导航长标签的表现如实保留在截图中，按阶段 2 的对应任务处理。
- 本项没有改动生产代码；真机五主题/三语言矩阵未验收，禁止为矩阵操作真实账号中的偏好设置。

## 1.4 减少动态效果

- 浏览器 `prefers-reduced-motion:reduce` 下，展开、选择、进度、滚轮、成功结果和页签导航可用；完成时粒子隐藏，活动动画数为 0，结果文字和静态对勾保留。
- 截图：`1.4-{selection,wheel,success,navigation}-static-light-zh.png`；断言记录 `1.4-reduced.json`。本项沿用既有减少动态效果实现，没有改动行为。
- 只读 ADB 检查时，真机三项动画比例均为 1.0、字号为 1.0；没有改动这些值。系统“移除动画”开启后的真机效果未验收，浏览器仿真通过不能替代该项。

## 1.5 动效逐帧

- `1.5-{completion,selection,stack,timeline,wheel,navigation,entry}-{before,middle,after}-light-zh.png` 共 21 张，另有 `1.5-contact.png` 联系表。入口跳转本身不增加转场。
- 浏览器 CSS/WAAPI 暂停到动作中段以捕获中间帧，随后结束动画捕获结果；滚轮和滚动按实际时间采样。`1.5-motion.json` 保存实际 timing：收缩 200、对勾 260、粒子 450、选择 180/220、卡片 240/错峰 28、圆形扩散 320ms，符合规范。
- 滚轮落到合法 60 天刻度；时间线停稳后更新当前项；成功结果保留静态文字。浏览器控制台无错误，真机逐帧未验收。没有录屏文件。
