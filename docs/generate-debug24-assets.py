"""Export the established vector UI language as individual transparent PNG assets."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys, json, hashlib, html, shutil, zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.android-tools/asset-tools'))
try:
    import resvg_py
except ImportError:
    raise SystemExit('Install resvg-py in .android-tools/asset-tools first; see assest/debug24/README.md.')
OUT=ROOT/'assest/debug24'
OUT.mkdir(parents=True,exist_ok=True)
paths=json.loads((ROOT/'.android-tools/debug24-icons.json').read_text(encoding='utf-8'))
groups={name:'system' for name in paths}
extra={
 'category-streaming':'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9 5 3-5 3z"/>',
 'category-ai':'<rect x="5" y="6" width="14" height="14" rx="3"/><path d="M12 3v3M9 11h.01M15 11h.01M9 16h6M2 11v5M22 11v5"/>',
 'category-gaming':'<path d="M7 7h10c3 0 5 11 3 12-2 1-4-4-5-4H9c-1 0-3 5-5 4C2 18 4 7 7 7zM7 9v5M4.5 11.5h5M16 10h.01M19 13h.01"/>',
 'category-server':'<rect x="3" y="3" width="18" height="7" rx="2"/><rect x="3" y="14" width="18" height="7" rx="2"/><path d="M7 6.5h.01M7 17.5h.01M11 6.5h6M11 17.5h6"/>',
 'category-sim':'<path d="M8 3h7l4 4v14H5V6z"/><rect x="8" y="10" width="8" height="7" rx="1"/><path d="M12 10v7M8 13.5h8"/>',
 'category-software':'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 8h18m-12 4-3 2 3 2m6-4 3 2-3 2"/>',
 'category-music':'<path d="M9 18V5l12-2v13M9 8l12-2"/><ellipse cx="6" cy="18" rx="3" ry="2.5"/><ellipse cx="18" cy="16" rx="3" ry="2.5"/>',
 'category-cloud':'<path d="M6 18a4 4 0 0 1-.7-7.94 7 7 0 0 1 13.4 0A4 4 0 0 1 18 18z"/>',
 'category-domain':'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18M5 7h14M5 17h14"/>',
 'category-membership':'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m8 9 2 3 2-4 2 4 2-3v6H8z"/>',
 'category-education':'<path d="m2 9 10-5 10 5-10 5zM6 11v6c4 3 8 3 12 0v-6M22 9v8"/>',
 'category-news':'<rect x="4" y="3" width="17" height="18" rx="2"/><path d="M4 7H2v12a2 2 0 0 0 2 2M8 7h9M8 11h3v4H8zM14 11h3M14 15h3M8 18h9"/>',
 'category-fitness':'<path d="m4 9 5-5m6 16 5-5M2 7l5-5M17 22l5-5M7 7l10 10M5 11l6-6M13 19l6-6"/>',
 'category-other':'<rect x="4" y="4" width="6" height="6" rx="1.5"/><rect x="14" y="4" width="6" height="6" rx="1.5"/><rect x="4" y="14" width="6" height="6" rx="1.5"/><rect x="14" y="14" width="6" height="6" rx="1.5"/>',
 'backup':'<path d="M5 15H3v6h18v-6h-2M7 15l5-5 5 5M12 10v11M5 7V3h14v4"/>',
 'restore':'<path d="M3 12a9 9 0 1 1 2.5 6.2M3 17v-5h5M12 7v6l4 2"/>',
 'sync':'<path d="M20 7a8 8 0 0 0-14-2L3 8M3 3v5h5M4 17a8 8 0 0 0 14 2l3-3M21 21v-5h-5"/>',
 'lock':'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/>',
 'shield':'<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6"/>',
 'filter':'<path d="M3 4h18l-7 8v7l-4 2v-9z"/>',
 'image':'<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 5-5 4 4 4-6 5 7"/>',
 'link':'<g transform="rotate(-45 12 12)"><rect x="3" y="8" width="9" height="8" rx="4"/><rect x="12" y="8" width="9" height="8" rx="4"/><path d="M9 12h6"/></g>',
 'eye':'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
 'eye-off':'<path d="m3 3 18 18M9 5.5A12 12 0 0 1 12 5c6 0 10 7 10 7a19 19 0 0 1-3 4M6 7a18 18 0 0 0-4 5s4 7 10 7a12 12 0 0 0 5-1M10 10a3 3 0 0 0 4 4"/>',
 'csv':'<path d="M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h8M11 10v9"/>',
 'sort':'<path d="M7 3v18M3 7l4-4 4 4M17 21V3M13 17l4 4 4-4"/>',
 'wifi-off':'<path d="m3 3 18 18M2 8a17 17 0 0 1 3-2M9 4.5A17 17 0 0 1 22 8M5 12a12 12 0 0 1 3-2M13 9a12 12 0 0 1 6 3M8 16a6 6 0 0 1 8 0M12 20h.01"/>',
 'language':'<path d="M3 5h12M9 3v2M5 5c1 5 4 8 8 10M13 5c-1 5-5 9-10 11M14 21l4-10 4 10M15.5 18h5"/>',
 'theme-light':'<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M19 5l-1.5 1.5M6.5 17.5 5 19"/>',
 'theme-dark':'<path d="M20.5 14a9 9 0 0 1-10.5-11A9 9 0 1 0 20.5 14z"/>',
 'fingerprint':'<path d="M5 12a7 7 0 0 1 14 0M8 14v-2a4 4 0 0 1 8 0v3c0 3-1 5-2 7M11 12v4c0 2-.5 4-2 6M5 16c0 2-.5 3-1 4M19 16v3M12 3a10 10 0 0 1 9 6"/>',
 'copy':'<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
 'save':'<path d="M4 3h13l4 4v14H3V3zM7 3v6h10V3M7 21v-8h10v8"/>',
 'pause':'<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
 'help':'<circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 0 1 6 0c0 2-3 2-3 5M12 17h.01"/>',
 'easysub-mark':'<rect x="3" y="3" width="18" height="18" rx="6"/><path d="m7 12 3.5 3.5 6.5-7"/>',
}
for name,path in extra.items():
    if name in paths:raise ValueError('Would overwrite established icon '+name)
    paths[name]=path;groups[name]='category' if name.startswith('category-') else 'brand' if name=='easysub-mark' else 'utility'

assets=[]
def export(name,path,color,variant):
    folder=OUT/'icons'/variant;folder.mkdir(parents=True,exist_ok=True)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="256" height="256" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">{path}</svg>'
    data=resvg_py.svg_to_bytes(svg_string=svg,width=256,height=256,skip_system_fonts=True)
    p=folder/(name+'.png');p.write_bytes(data)
    with Image.open(p) as image:
        assert image.mode=='RGBA',p
        alpha=image.getchannel('A');assert alpha.getextrema()[0]==0 and alpha.getextrema()[1]>0,p
        assert all(alpha.getpixel(point)==0 for point in [(0,0),(255,0),(0,255),(255,255)]),p
        box=alpha.getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<256 and box[3]<256,p
    assets.append(dict(name=name,group=groups[name],variant=variant,path=p.relative_to(OUT).as_posix(),width=256,height=256,transparent=True,sha256=hashlib.sha256(data).hexdigest(),source='frontend/src/icons.js' if name not in extra else 'debug24 vector extension'))

for variant,color in [('light','#16191d'),('dark','#eceef0')]:
    for name,path in paths.items():export(name,path,color,variant)
for variant,color in [('active-light','#0f7352'),('active-dark','#3dd68c')]:
    for name in ['dashboard','subscriptions','calendar','reports','settings']:export(name,paths[name],color,variant)
for theme in ['light','dark']:
    p=OUT/'backgrounds'/f'onboarding-{theme}.png'
    if not p.exists():raise ValueError('Missing generated background '+str(p))
    with Image.open(p) as image:width,height=image.size
    assets.append(dict(name='onboarding-'+theme,group='background',variant=theme,path=p.relative_to(OUT).as_posix(),width=width,height=height,transparent=False,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source='imagegen, generated for debug24'))

(OUT/'manifest.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2),encoding='utf-8')
brand_paths=json.loads((ROOT/'frontend/src/android-preview/cached-icons.json').read_text(encoding='utf-8'))
(OUT/'existing-brand-library.json').write_text(json.dumps(dict(note='Existing provider artwork is indexed, not regenerated or falsely labelled transparent. Original trademark assets remain in frontend/public/preview-icons.',icons=brand_paths),ensure_ascii=False,indent=2),encoding='utf-8')
readme=f'''# debug24 图片素材

共 {len(paths)} 种系统/分类/工具/应用标记图形，导出浅色与深色透明 PNG；另有五项导航的两套选中态，以及 2 张 AI 生成的引导页背景。

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
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
cards=[]
for a in assets:
    cls='dark' if a['variant'] in ['dark','active-dark'] else 'light'
    if a['group']=='background':cls+=' background'
    cards.append(f'<article class="{cls}" data-name="{a["name"]}" data-variant="{a["variant"]}"><a href="{a["path"]}" target="_blank"><div class="tile"><img loading="lazy" src="{a["path"]}" alt="{html.escape(a["name"])}"/></div></a><b>{a["name"]}</b><small>{a["variant"]} · {a["width"]}×{a["height"]} · {"透明" if a["transparent"] else "背景"}</small><a href="{a["path"]}" download>下载 PNG</a></article>')
doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EasySub · debug24 素材库</title><style>*{box-sizing:border-box}body{margin:0;color:#16191d;background:#f6f7f5;font:14px/1.6 'Microsoft YaHei',system-ui,sans-serif}header{padding:32px clamp(20px,5vw,64px);border-bottom:1px solid #cfd3d2}h1{font-size:32px;margin:8px 0}p{max-width:900px;color:#59606a}.tools{display:flex;gap:12px;flex-wrap:wrap}input,select,a.action{font:inherit;min-height:44px;border:1px solid #cfd3d2;border-radius:10px;padding:10px 14px;background:white;color:#16191d}a{color:#0f7352}main{padding:24px clamp(20px,4vw,56px);display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:24px}article{min-width:0}article b,article small{display:block;overflow-wrap:anywhere}article small{color:#59606a;font-size:12px}.tile{height:140px;display:grid;place-items:center;border:1px solid #e1e4e3;border-radius:14px;background-color:white;background-image:linear-gradient(45deg,#f0f1ef 25%,transparent 25%),linear-gradient(-45deg,#f0f1ef 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#f0f1ef 75%),linear-gradient(-45deg,transparent 75%,#f0f1ef 75%);background-size:16px 16px;background-position:0 0,0 8px,8px -8px,-8px 0}article.dark .tile{background-color:#171a1e;background-image:linear-gradient(45deg,#24292f 25%,transparent 25%),linear-gradient(-45deg,#24292f 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#24292f 75%),linear-gradient(-45deg,transparent 75%,#24292f 75%)}img{display:block;width:56px;height:56px;object-fit:contain}.background{grid-column:span 2}.background .tile{height:360px}.background img{width:100%;height:100%;object-fit:contain}article[hidden]{display:none}:focus-visible{outline:3px solid #0f7352;outline-offset:3px}@media(max-width:400px){.background{grid-column:span 1}}</style><header><small>EASYSUB / DEBUG24 / IMAGE ASSETS</small><h1>统一的界面素材库</h1><p>系统图标保留现有线性风格并导出透明 PNG；引导页背景分别提供浅色和深色版本。商家原图仍由原有图库提供。透明棋盘格仅用于此预览页面，不在 PNG 中。</p><div class="tools"><input id="search" type="search" placeholder="搜索素材名称" aria-label="搜索素材"><select id="variant" aria-label="选择主题"><option value="">全部主题</option><option>light</option><option>dark</option><option>active-light</option><option>active-dark</option></select><a class="action" href="README.md">使用说明</a><a class="action" href="manifest.json">清单与校验</a></div><p id="count"></p></header><main>CARDS</main><script>function filter(){let n=0;const q=document.querySelector('#search').value.toLowerCase(),v=document.querySelector('#variant').value;document.querySelectorAll('article').forEach(el=>{el.hidden=!(el.dataset.name.includes(q)&&(!v||el.dataset.variant===v));if(!el.hidden)n++});document.querySelector('#count').textContent='显示 '+n+' 个素材'}document.querySelector('#search').oninput=filter;document.querySelector('#variant').onchange=filter;filter();</script></html>'''
(OUT/'index.html').write_text(doc.replace('CARDS',''.join(cards)),encoding='utf-8')

# Contact sheet of both themes for inspection; it is a preview, not a runtime icon.
cols=8;cellw=164;cellh=126;rows=(len(paths)+cols-1)//cols
sheet=Image.new('RGB',(cols*cellw,(rows*cellh+60)*2),'#f6f7f5');draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',12)
for variant,bg,fg,section in [('light','#f6f7f5','#16191d',0),('dark','#171a1e','#eceef0',1)]:
    top=section*(rows*cellh+60);draw.rectangle((0,top,cols*cellw,top+rows*cellh+60),fill=bg);draw.text((20,top+15),'EasySub / '+variant+' / transparent PNG',font=font,fill=fg)
    for i,name in enumerate(paths):
        x=(i%cols)*cellw;y=top+52+(i//cols)*cellh
        with Image.open(OUT/'icons'/variant/(name+'.png')) as image:
            icon=image.resize((50,50),Image.Resampling.LANCZOS);sheet.paste(icon,(x+56,y+8),icon)
        draw.text((x+10,y+73),name,font=font,fill=fg)
sheet.save(OUT/'preview.png')
zip_path=ROOT/'artifacts/design/EasySub-debug24-assets.zip';zip_path.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as archive:
    for p in OUT.rglob('*'):
        if p.is_file():archive.write(p,p.relative_to(OUT))
print(json.dumps(dict(unique_icon_shapes=len(paths),transparent_pngs=sum(a['transparent'] for a in assets),background_pngs=2,total_png_assets=len(assets),path=str(OUT),zip=str(zip_path)),ensure_ascii=True))
