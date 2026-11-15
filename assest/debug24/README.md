# debug24 图片素材

共 75 种系统/分类/工具/应用标记图形，导出浅色与深色透明 PNG；另有五项导航的两套选中态，以及 2 张 AI 生成的引导页背景。

## 文件

- icons/light：墨色描边，每个图标一个 256×256 RGBA PNG。
- icons/dark：浅色描边，每个图标一个 256×256 RGBA PNG。
- icons/active-light、icons/active-dark：五项导航选中状态。
- backgrounds/onboarding-light.png、onboarding-dark.png：不透明引导页背景，大面积留白。
- manifest.json：用途、主题、尺寸、透明状态、来源与 SHA256。
- index.html：可离线预览和下载单个素材。

所有本次导出的图标均检查了 alpha 通道和透明四角。背景图片本身需要承载底色，因此不是透明背景。

## 用法

通常以 16、20、24 CSS px 使用系统图标，品牌标记按场景使用 32/40。PNG 导出不改变源 SVG，描边和主题切换、对勾一笔绘制仍建议用现有 SVG 实现。不要将 PNG 动画拉伸为模糊图形。

背景仅用于引导页/说明页；不要覆盖订阅列表、表单、图表等核心信息页面。留白中央用于文字和操作，按图片比例缩放，不能为了铺满裁掉所有主题元素。

商家标志使用现有 323 张图库，不由 AI 猜画。已有图库中部分文件本身为不透明品牌标志，本次只索引其来源，未伪称已经去除背景，也未修改原始商标。设计草图中的首字占位不作为官方商标交付。

目录沿用用户要求的拼写 assest。当前交付是图片素材，不会自动替换线上图标。

## 重新导出

先用 Node 将 frontend/src/icons.js 的默认导出写到 .android-tools/debug24-icons.json，再安装 resvg-py 到 .android-tools/asset-tools，运行 python docs/generate-debug24-assets.py。本地工具不加入 App 运行时依赖。
