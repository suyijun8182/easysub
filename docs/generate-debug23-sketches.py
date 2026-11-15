"""Generate offline SVG/PNG mobile design boards using synthetic data only."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, math, html, zipfile, shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/design/debug23'
OUT.mkdir(parents=True, exist_ok=True)
for folder in ['screens', 'boards']:
    (OUT / folder).mkdir(exist_ok=True)
FONT = 'C:/Windows/Fonts/msyh.ttc'
BOLD = 'C:/Windows/Fonts/msyhbd.ttc'
W, H, SCALE = 390, 844, 2
LIGHT = dict(bg='#f6f7f5', surface='#ffffff', muted='#eef0ee', ink='#16191d', sub='#59606a', line='#e1e4e3', green='#0f7352', soft='#e3f3ec', amber='#9e5b00', warm='#fdf1dc', red='#c3352c', rose='#fbe6e3', action='#1b1f24', on='#ffffff')
DARK = dict(bg='#0f1113', surface='#171a1e', muted='#1f2328', ink='#eceef0', sub='#9aa2ad', line='#353b42', green='#3dd68c', soft='#12291f', amber='#f5b83d', warm='#2e2512', red='#ff6b5e', rose='#32191a', action='#eceef0', on='#111315')

class Canvas:
    def __init__(self, dark=False):
        self.t = DARK if dark else LIGHT
        self.im = Image.new('RGB', (W*SCALE,H*SCALE), self.t['bg'])
        self.d = ImageDraw.Draw(self.im)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="390" height="844" viewBox="0 0 390 844"><rect width="390" height="844" fill="{self.t["bg"]}"/>']
    def color(self, value): return self.t.get(value,value)
    def box(self,x,y,w,h,fill='surface',radius=12,stroke=None):
        fill=self.color(fill); st=self.color(stroke) if stroke else None
        self.d.rounded_rectangle(tuple(round(v*SCALE) for v in (x,y,x+w,y+h)),radius=round(radius*SCALE),fill=fill,outline=st,width=SCALE if st else 1)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"'+(f' stroke="{st}"' if st else '')+'/>')
    def line(self,x1,y1,x2,y2,color='line',width=1):
        color=self.color(color);self.d.line(tuple(round(v*SCALE) for v in (x1,y1,x2,y2)),fill=color,width=max(1,round(width*SCALE)))
        self.svg.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>')
    def circle(self,x,y,r,fill='soft',stroke=None,width=1):
        fill=self.color(fill);st=self.color(stroke) if stroke else None
        self.d.ellipse(tuple(round(v*SCALE) for v in (x-r,y-r,x+r,y+r)),fill=fill,outline=st,width=max(1,round(width*SCALE)))
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"'+(f' stroke="{st}" stroke-width="{width}"' if st else '')+'/>')
    def text(self,txt,x,y,size=14,color='ink',bold=False,maxw=None,lines=3):
        txt=str(txt);font=ImageFont.truetype(BOLD if bold else FONT,round(size*SCALE));parts=[];part=''
        for ch in txt:
            if ch=='\n' or (maxw and self.d.textlength(part+ch,font=font)>maxw*SCALE):
                parts.append(part);part='' if ch=='\n' else ch
            else:part+=ch
        parts.append(part)
        for i,part in enumerate(parts[:lines]):
            yy=y+i*size*1.5
            self.d.text((round(x*SCALE),round(yy*SCALE)),part,font=font,fill=self.color(color),stroke_width=0)
            self.svg.append(f'<text x="{x}" y="{yy+size*.96}" font-family="Microsoft YaHei, PingFang SC, sans-serif" font-size="{size}" font-weight="{650 if bold else 400}" fill="{self.color(color)}">{html.escape(part)}</text>')
        return y+min(len(parts),lines)*size*1.5
    def right(self,txt,x,y,size=14,color='ink',bold=False):
        font=ImageFont.truetype(BOLD if bold else FONT,round(size*SCALE));width=self.d.textlength(str(txt),font=font)/SCALE
        return self.text(txt,x-width,y,size,color,bold)
    def icon(self,name,x,y,size=20,color='sub'):
        q=size/20
        def ln(a,b,c,d):self.line(x+a*q,y+b*q,x+c*q,y+d*q,color,1.7)
        if name=='back':ln(12,4,6,10);ln(6,10,12,16)
        elif name=='next':ln(7,4,13,10);ln(13,10,7,16)
        elif name=='down':ln(4,7,10,13);ln(10,13,16,7)
        elif name=='check':ln(4,10,8,14);ln(8,14,16,5)
        elif name=='plus':ln(4,10,16,10);ln(10,4,10,16)
        elif name=='close':ln(5,5,15,15);ln(15,5,5,15)
        elif name=='grid':
            for a,b in [(2,2),(11,2),(2,11),(11,11)]:self.box(x+a*q,y+b*q,6*q,6*q,'bg',1,color)
        elif name=='calendar':
            self.box(x+2*q,y+4*q,16*q,14*q,'surface',2,color);ln(2,9,18,9);ln(6,2,6,6);ln(14,2,14,6)
        elif name=='chart':ln(4,17,4,11);ln(10,17,10,4);ln(16,17,16,8)
        elif name=='card':self.box(x+2*q,y+4*q,16*q,12*q,'surface',2,color);ln(3,9,17,9)
        elif name=='search':self.circle(x+8*q,y+8*q,5*q,'surface',color,1.6);ln(12,12,17,17)
        else:
            self.circle(x+10*q,y+10*q,6*q,'bg',color,1.6)
            for a in range(0,360,60):
                r=math.radians(a);ln(10+7*math.cos(r),10+7*math.sin(r),10+9*math.cos(r),10+9*math.sin(r))
    def status(self):
        self.text('9:41',24,12,12,bold=True)
        for i in range(3):self.box(312+i*4,22-i*3,2,3+i*3,'ink',.5)
        self.box(334,17,24,11,'bg',3,'sub');self.box(337,20,17,5,'ink',1)
    def header(self,title='',root=False):
        self.status()
        if root:
            self.box(20,52,26,26,'soft',9);self.icon('check',23,55,20,'green');self.text('EasySub',55,51,20,bold=True)
            self.text('ALPHA',144,58,9,'sub',True);self.circle(347,65,21,'surface','line');self.icon('settings',337,55,20)
        else:
            self.icon('back',20,55,22);self.text(title,53,52,17,bold=True);self.icon('settings',338,55,20)
    def title(self,title,sub=None,y=108):
        self.text(title,20,y,24,bold=True)
        if sub:self.text(sub,20,y+39,12,'sub',maxw=350)
    def nav(self,active=0):
        self.box(0,768,390,76,'surface',0);self.line(0,768,390,768)
        for i,(name,ico) in enumerate(zip(['总览','订阅','日历','报表','设置'],['grid','card','calendar','chart','settings'])):
            x=39+i*78
            if i==active:self.box(x-26,775,52,31,'soft',13)
            self.icon(ico,x-10,780,20,'green' if i==active else 'sub');self.text(name,x-12,811,11,'green' if i==active else 'sub',i==active)
        self.box(151,837,88,3,'ink',2)
    def button(self,label,y=766,x=20,w=350,kind='action'):
        self.box(x,y,w,48,kind,12,'line' if kind=='surface' else None)
        size=14;font=ImageFont.truetype(BOLD,size*SCALE);tw=self.d.textlength(label,font=font)/SCALE
        self.text(label,x+(w-tw)/2,y+13,size,'on' if kind=='action' else 'ink',True)
    def logo(self,label,x,y,size=36):
        self.box(x,y,size,size,'muted',size*.27);self.text(label[0].upper(),x+size*.27,y+size*.12,size*.55,'ink',True)
    def pill(self,label,x,y,kind='soft',w=None):
        w=w or len(label)*12+22;self.box(x,y,w,27,kind,14);self.text(label,x+11,y+5,11,'green' if kind=='soft' else 'sub',True)
    def row(self,title,sub='',right='',y=190,logo=None,checked=False,h=70):
        if checked:self.box(20,y-2,350,h-2,'soft',14,'green')
        x=32
        if logo:self.logo(logo,x,y+12);x+=48
        self.text(title,x,y+10,14,bold=True,maxw=210)
        if sub:self.text(sub,x,y+35,11,'sub',maxw=236,lines=1)
        if right:self.right(right,355,y+14,13,'green' if checked else 'ink',True)
        self.line(32,y+h-1,358,y+h-1)
    def field(self,label,value,y=180,h=66):
        self.text(label,22,y,12,'sub');self.box(20,y+23,350,h-29,'surface',12,'line');self.text(value,33,y+32,14,maxw=320,lines=1)
    def note(self,title,body,y=600,kind='muted',h=85):
        self.box(20,y,350,h,kind,14);self.text(title,34,y+12,13,bold=True);self.text(body,34,y+37,12,'sub',maxw=318,lines=2)
    def bar(self,label,value,total,y,color='green'):
        self.text(label,20,y,13);self.right(str(value),370,y,13,bold=True);self.box(20,y+27,350,7,'muted',4);self.box(20,y+27,max(7,350*total),7,color,4)
    def ring(self,x,y,r,progress=.35):
        self.circle(x,y,r,'bg','line',4)
        if progress:
            b=tuple(round(v*SCALE) for v in (x-r,y-r,x+r,y+r));self.d.arc(b,-90,-90+360*progress,fill=self.color('green'),width=4*SCALE)
            end=-math.pi/2+2*math.pi*progress;ex=x+r*math.cos(end);ey=y+r*math.sin(end)
            self.svg.append(f'<path d="M{x} {y-r} A{r} {r} 0 {1 if progress>.5 else 0} 1 {ex} {ey}" fill="none" stroke="{self.color("green")}" stroke-width="4"/>')
    def save(self,slug):
        self.im.save(OUT/'screens'/f'{slug}.png')
        (OUT/'screens'/f'{slug}.svg').write_text(''.join(self.svg)+'</svg>',encoding='utf-8')
    def shade(self):
        overlay=Image.new('RGBA',self.im.size,(15,23,18,100))
        self.im=Image.alpha_composite(self.im.convert('RGBA'),overlay).convert('RGB');self.d=ImageDraw.Draw(self.im)
        self.svg.append('<rect width="390" height="844" fill="#0f1712" opacity=".39"/>')

SCREENS=[]
def add(slug,title,group,kind='form',data=None,note='',state='设计方案'):
    SCREENS.append(dict(id=slug,title=title,group=group,kind=kind,data=data or [],note=note,state=state))

add('01-home','总览','01 核心页面','home')
add('02-subscriptions','订阅列表','01 核心页面','subscriptions')
add('03-detail','订阅详情','01 核心页面','detail')
add('04-new-service','新增 · 选择服务','02 新增与编辑','services')
add('05-library','服务库 · 分类浏览','02 新增与编辑','rows',[('VPS / 服务器','供应商与套餐','128 家'),('视频与音乐','流媒体与内容','76 家'),('SIM / eSIM','保号与流量','94 家'),('软件与 AI','效率与创作','83 家'),('存储与域名','云盘、域名、托管','65 家'),('其他分类','全部 13 类','查看')],note='供应商数量仅用于版式演示。')
add('06-icons','服务图标','02 新增与编辑','icons')
add('07-new-basic','新增 · 服务与价格','02 新增与编辑','form',[('服务名称','DMIT'),('套餐','Premium · Tokyo'),('个性化备注','东京主机 · 工作使用'),('价格 / 币种','38.50       USD'),('分类 / 支付方式','VPS / 服务器    信用卡')])
add('08-new-billing','新增 · 周期与日期','02 新增与编辑','form',[('计费方式','循环订阅     /     一次性买断'),('周期','1       月'),('开始日期','2026-11-01'),('下次计费日期','2026-12-01 · 自动计算'),('提前提醒','7, 6, 5, 4, 3, 2, 1 天'),('状态','启用 · 自动续费 · 日历可见')])
add('09-new-network','新增 · 网络与共享','02 新增与编辑','form',[('IPv4（选填）','192.0.2.24'),('IPv6（选填）','2001:db8::24'),('家庭成员','成员 A     ＋ 添加'),('捆绑包','加入已有 / 创建 / 不使用'),('官方网站','https://example.test'),('详细备注','用途、合同或补充信息')])
add('10-new-risk','新增 · 风险与卡片','02 新增与编辑','form',[('试用结束','2026-11-15'),('取消截止','2026-11-13'),('付款卡末四位','2841'),('付款卡有效期','09 / 2028'),('个别提醒规则','使用默认规则 / 自定义')])
add('11-new-review','新增 · 保存前核对','02 新增与编辑','rows',[('DMIT','东京主机 · Premium Tokyo','38.50 USD'),('计费周期','从 2026-11-01 开始','每月'),('下次到期','按开始日自动计算','12月1日'),('分类与支付','VPS / 服务器','信用卡'),('提醒与扩展资料','倒数 7 天每天提醒','已填写')],note='保存后保留在手机，并按账号设置同步。')
add('12-edit','编辑订阅','02 新增与编辑','form',[('服务名称','DMIT'),('套餐与备注','Premium · 东京主机'),('价格 / 币种','38.50      USD'),('周期 / 下次到期','1 月     2026-12-01'),('更多资料','网络、家庭、付款卡与风险日期')])
add('13-renewals','续费计划','03 debug23 交互','renewals')
add('14-selected','勾选与进度联动','03 debug23 交互','renewals',note='selected')
add('15-stack','卡片堆叠 · 收起','03 debug23 交互','stack')
add('16-expanded','卡片堆叠 · 展开','03 debug23 交互','expanded')
add('17-timeline','吸附卡片与时间线','03 debug23 交互','timeline')
add('18-wheel','惯性滚轮 · 范围选择','03 debug23 交互','wheel')
add('19-renew-confirm','续费核对面板','03 debug23 交互','sheet',[('DMIT','东京主机 · 38.50 USD'),('VOXI','保号号码 •••• 2841 · 0.20 EUR'),('起算方式','从今天 / 从原到期日')],note='仅记录已完成续费，不执行扣款。')
add('20-renew-saving','完成反馈 · 保存中','03 debug23 交互','feedback',note='saving')
add('21-renew-success','完成反馈 · 已保存','03 debug23 交互','feedback',note='success')
add('22-renew-partial','完成反馈 · 部分失败','03 debug23 交互','feedback',note='partial')
add('23-actions','订阅操作菜单','04 列表管理','sheet',[('查看详情','完整字段与记录'),('编辑订阅','修改服务、金额和日期'),('记录续费','核对新的起算方式'),('暂停 / 恢复','保留所有资料'),('删除订阅','需要二次确认')])
add('24-delete','删除确认','04 列表管理','sheet',[('DMIT','东京主机 · Premium · 38.50 USD'),('确认删除','键入订阅名称确认'),('身份校验','设备认证接入前使用明确确认')],note='设计目标；原生设备认证尚未完成。')
add('25-bulk','批量管理','04 列表管理','bulk')
add('26-sort','订阅与分类排序','04 列表管理','rows',[('VPS / 服务器','整组移动','↑ ↓'),('DMIT','仅在当前分类内排序','↑ ↓'),('BandwagonHost','仅在当前分类内排序','↑ ↓'),('SIM / 保号','整组移动','↑ ↓'),('VOXI','可拖动，也可点按上下移','↑ ↓')])
add('27-csv','CSV 导入与导出','04 列表管理','rows',[('导出当前订阅','保留字段名与 UTF-8 编码','导出'),('导入 CSV','从系统文件选择器打开','选择'),('预览导入结果','显示新增、重复、错误行','核对'),('冲突处理','逐项选择，不静默覆盖','设置')])
add('28-calendar','月历','05 日历与报表','calendar')
add('29-day','当日议程','05 日历与报表','rows',[('11月15日 · 星期日','共 3 项，按时间排列','日程'),('DMIT','东京主机 · 信用卡','38.50 USD'),('iCloud+','家庭存储 · 自动续费','6.00 CNY'),('VOXI','保号号码 •••• 2841','0.20 EUR')])
add('30-ics','导出系统日历','05 日历与报表','form',[('导出范围','启用且允许日历显示的订阅'),('包含信息','名称、金额、备注、提前提醒'),('保存方式','选择系统文件目录')],note='ICS 是文件快照，资料更新后需要重新导出。')
add('31-reports','报表总览','05 日历与报表','reports')
add('32-insights','支出洞察','05 日历与报表','rows',[('支出排行','按折算后的月支出排序','查看'),('DMIT','东京主机 · 预算占比 24%','38.50 USD'),('即将续费','未来 30 天 6 项','¥286.40'),('一次性买断','保留累计成本，不计为循环月费','¥1,248'),('已过期项目','需要处理的事项','2 项')])
add('33-category-report','分类明细','05 日历与报表','bars')
add('34-recent-payments','近期付款记录','05 日历与报表','rows',[('2026年11月','仅展示有记录的付款','筛选'),('iCloud+','家庭存储 · 11月1日','6.00 CNY'),('DMIT','东京主机 · 10月28日','38.50 USD'),('ChatGPT Plus','创作工具 · 10月22日','20.00 USD'),('导出报表','当前筛选范围','CSV')],note='真实付款与周期成本估算须明确区分。')
add('35-settings','设置','06 设置与管理','settings')
add('36-appearance','外观、语言与预算','06 设置与管理','form',[('主题','跟随系统 / 浅色 / 深色'),('其他主题','海洋 / 森林 / 紫色'),('语言','中文 / English / Русский'),('基准货币','CNY 人民币'),('月预算','500.00 CNY')])
add('37-reminders','提醒计划','06 设置与管理','form',[('默认提前提醒','7, 6, 5, 4, 3, 2, 1 天'),('免打扰时间','22:00 — 08:00'),('每周摘要','周一 09:00'),('通知权限','查看系统授权状态'),('后台能力','显示系统限制与最近执行结果')],note='原生系统通知与后台任务为设计目标，当前 Alpha 尚未完整实现。')
add('38-channels','外部通知渠道','06 设置与管理','rows',[('Telegram Bot / 飞书 Bot','独立配置与测试','2 渠道'),('QQ Bot / Bark / Email','独立配置与测试','3 渠道'),('Pushplus / Server酱 / 企业微信','独立配置与测试','3 渠道'),('钉钉 / Discord / Slack','独立配置与测试','3 渠道'),('ntfy / Gotify / Webhook','独立配置与测试','3 渠道')],note='全部 14 个渠道均有独立配置草图。')
CHANNELS=[('telegram','Telegram Bot',[('BOT TOKEN','••••••••••••'),('CHAT ID','示例接收会话'),('ADMIN ID','可选'),('API 地址','https://api.telegram.org'),('代理','可选')]),('feishu','飞书 Bot',[('Webhook 地址','https://example.test/hook'),('签名密钥','••••••••')]),('qq','QQ Bot',[('APP ID','示例应用'),('APP SECRET','••••••••'),('群 / 用户 ID','按接收对象填写')]),('bark','Bark',[('服务器','https://api.day.app'),('设备 Key','••••••••'),('分组 / 声音','EasySub / 默认')]),('email','Email',[('SMTP 主机与端口','smtp.example.test : 465'),('发件地址','notice@example.test'),('用户名与密码','••••••••'),('收件地址','demo@example.test'),('传输安全','SSL / STARTTLS')]),('pushplus','Pushplus',[('Token','••••••••'),('群组 / 模板','可选 / HTML')]),('serverchan','Server酱',[('SendKey','••••••••')]),('wecom','企业微信',[('发送模式','群机器人 / 自建应用'),('企业 ID / Agent ID','示例企业 / 应用'),('Secret','••••••••'),('接收成员与部门','按应用可见范围填写'),('代理地址','可选')]),('dingtalk','钉钉',[('Webhook 地址','https://example.test/hook'),('加签密钥','••••••••')]),('discord','Discord',[('Webhook 地址','https://example.test/hook'),('显示名称','EasySub')]),('slack','Slack',[('Webhook 地址','https://example.test/hook'),('频道','可选')]),('ntfy','ntfy',[('服务器','https://ntfy.sh'),('Topic','easysub-demo'),('Token / 用户密码','••••••••')]),('gotify','Gotify',[('服务器','https://example.test'),('应用 Token','••••••••'),('优先级','5')]),('webhook','Webhook',[('URL / Method','https://example.test / POST'),('Headers','Content-Type: application/json'),('Body 模板','title、message 与订阅变量'),('认证密钥','••••••••')])]
for key,name,fields in CHANNELS:add('channel-'+key,name+' 配置','07 通知渠道',data=fields,note='联网发送需实际渠道验证；密钥默认隐藏。')
channel_fields = {
 'feishu': [('APP ID','示例飞书应用'),('APP SECRET','••••••••'),('接收会话 ID','多个 Chat ID 分开填写')],
 'bark': [('设备推送 URL 列表','https://example.test/device-key'),('分组','EasySub'),('通知级别','active'),('通知图标 URL','可选')],
 'pushplus': [('Token','••••••••'),('Topic / 群组','可选'),('投递渠道','wechat')],
 'discord': [('Webhook 地址','https://example.test/hook')],
 'slack': [('Webhook 地址','https://example.test/hook')],
 'ntfy': [('服务器','https://ntfy.sh'),('Topic','easysub-demo'),('访问 Token','••••••••')],
 'webhook': [('推送 URL 列表','https://example.test/hook'),('签名密钥','••••••••'),('Headers','Content-Type: application/json'),('Body 模板','title、message 与订阅变量')]
}
for s in SCREENS:
    if s['id'].startswith('channel-') and s['id'][8:] in channel_fields:s['data']=channel_fields[s['id'][8:]]
add('channel-wecom-robot','企业微信 · 群机器人','07 通知渠道',data=[('发送模式','群机器人'),('机器人 Webhook','https://example.test/wecom-hook')],note='与自建应用共用一个渠道入口，切换模式不丢失配置。')
add('channel-wecom-advanced','企业微信 · 投递选项','07 通知渠道',data=[('成员 / 部门 / 标签','分别指定接收范围'),('消息类型','文本 / Markdown / 卡片'),('卡片跳转地址','https://example.test'),('代理服务器','可选')])
add('channel-webhook-advanced','Webhook · 重试策略','07 通知渠道',data=[('请求超时','5000 毫秒'),('最大重试次数','3 次'),('多个推送目标','逐项显示发送结果')])
add('53-categories','分类管理','08 资料管理','rows',[('VPS / 服务器','3 项订阅','编辑'),('SIM / 保号','5 项订阅','编辑'),('软件与 AI','8 项订阅','编辑'),('视频与音乐','4 项订阅','编辑'),('新增分类','名称、图标、颜色与排序','＋')])
add('54-payment-methods','支付方式','08 资料管理','rows',[('信用卡','末四位 •••• 2841','编辑'),('支付宝','日常账单','编辑'),('PayPal','海外订阅','编辑'),('新增支付方式','名称与图标','＋')])
add('55-bundles','捆绑包','08 资料管理','rows',[('家庭共享','3 个成员 · 4 项订阅','查看'),('工作服务','2 项订阅 · 独立总价','查看'),('创建捆绑包','可添加成员与服务','＋')])
add('56-currencies','币种与汇率','08 资料管理','form',[('基准货币','CNY'),('USD → CNY','7.12 · 演示汇率'),('EUR → CNY','7.76 · 演示汇率'),('最近更新','2026-11-01 09:30'),('自定义货币','代码、名称、符号、手动汇率')],note='离线使用缓存；汇率缺失时不显示误导性的零成本。')
add('57-backup','备份与恢复','09 备份恢复','rows',[('导出加密备份','包含密钥、图标与关联资料','导出'),('恢复备份','JSON 或加密备份','选择'),('安全副本','恢复前先保留当前资料','查看'),('自动备份','目录权限与后台执行','规划中')],note='备份密码不保存，丢失后无法恢复。')
add('58-export','导出加密备份','09 备份恢复','form',[('备份内容','订阅、设置、图标、通知密钥'),('加密密码','••••••••••'),('再次输入密码','••••••••••'),('保存位置','系统文件选择器')],note='密钥始终加密导出，不提供无保护的导出选项。')
add('59-restore-file','恢复 · 选择文件','09 备份恢复','form',[('备份文件','easysub-demo.encrypted.json'),('解密密码','••••••••••'),('备份来源','个人备份 / 整站备份'),('选择用户','整站备份需选一个资料库')])
add('60-restore-preview','恢复 · 内容预览','09 备份恢复','rows',[('订阅','其中重复 3 项','31 项'),('分类 / 支付方式','保留原关联','8 / 4'),('图标与通知密钥','密钥不在预览中显示','已包含'),('预算与币种','已识别基准汇率','完整'),('风险提示','备份日期 2026-10-30','核对')])
add('61-restore-mode','恢复 · 方式与确认','09 备份恢复','sheet',[('追加恢复','保留当前资料，跳过相同项'),('替换恢复','先创建安全副本，再替换'),('确认目标','当前手机资料库')],note='替换前明确显示影响范围，不能默认执行。')
add('62-restore-result','恢复 · 结果','09 备份恢复','result',note='已恢复 28 项，跳过 3 项重复记录。安全副本已保留。')
add('63-sync-login','连接网页账号','10 账号与同步','form',[('服务器网址','https://example.test'),('网页用户名','demo-account'),('密码','••••••••••'),('两步验证码','启用时填写')],note='测试连接后先核对账号，不立即合并。')
add('64-sync-review','同步 · 身份核对','10 账号与同步','sheet',[('服务器 / 账号','example.test · demo-account'),('本地订阅 / 网页订阅','12 项 / 31 项'),('首次合并','保留双方；同名不同身份不删除'),('设置与通知密钥','有差异时保留双方供选择')])
add('65-sync-status','同步 · 正常状态','10 账号与同步','rows',[('demo-account','example.test · 已连接','正常'),('上次完成','今天 09:41','成功'),('待上传 / 待处理','未解决冲突会单独列出','0 / 0'),('立即同步','前台自动检查已开启','同步'),('暂停或退出','退出仅清除登录令牌','管理')])
add('66-conflict','同步 · 冲突处理','10 账号与同步','conflict')
add('67-security','账号与安全','10 账号与同步','rows',[('密码与邮箱','在网页端管理','网页入口'),('两步验证','启用 / 恢复码管理','网页入口'),('API Token','由服务器提供','网页入口'),('注册与验证码','已有账号可直接登录','网页入口'),('Home Assistant','服务器服务接口','网页入口')],note='外部网页能力明确标注，不伪装成本地已实现。')
add('68-register','注册与邮箱验证','10 账号与同步','form',[('用户名','demo-account'),('邮箱','demo@example.test'),('验证码','6 位邮箱验证码'),('密码','••••••••••'),('账号启用','验证成功后直接使用')],state='网页流程设计')
add('69-notifications','通知记录','11 记录与系统','rows',[('今天','提醒记录与实际发送结果','3 条'),('DMIT · 提前 7 天','Telegram · 已发送','09:00'),('VOXI · 保号提醒','本地通知 · 待原生接入','规划'),('发送失败','网络不可用，可查看原因','重试')])
add('70-logs','操作日志','11 记录与系统','rows',[('09:41 · 同步完成','记录数量与来源，不记录密钥','info'),('09:32 · 修改订阅','DMIT · 东京主机','info'),('昨天 · 恢复预览','未提交替换操作','info'),('筛选日志','级别 / 时间 / 搜索','筛选')])
add('71-privacy','应用隐私与锁定','11 记录与系统','form',[('本地加密存储','Android Keystore'),('应用锁','设备认证接入后可开启'),('多任务预览保护','原生能力规划'),('敏感资料导出','始终使用加密备份')],state='含原生能力规划')
add('72-about','关于与更新','11 记录与系统','rows',[('EasySub','Android Alpha · 设计示意','版本'),('检查更新','签名一致时覆盖升级','检查'),('项目与反馈','GitHub Releases','打开'),('作者信息','联系方式与开源许可','查看'),('升级提示','保留本地数据与加密密钥','说明')])
add('73-admin','管理员网页入口','11 记录与系统','rows',[('用户管理','由网页管理员功能提供','网页入口'),('整站备份','管理员导出所有用户资料','网页入口'),('整站恢复','核对目标和数据影响','网页入口')],state='网页功能边界')
add('74-onboarding','首次启动 · 本地优先','12 状态与适配','onboarding')
add('75-empty','空订阅状态','12 状态与适配','empty')
add('76-loading','加载与恢复中','12 状态与适配','loading')
add('77-offline','离线与待上传','12 状态与适配','offline')
add('78-error','错误与重试','12 状态与适配','error')
add('79-dark-home','深色 · 总览','12 状态与适配','home',note='dark')
add('80-dark-renewals','深色 · 续费计划','12 状态与适配','renewals',note='dark selected')
add('81-large-text','放大字号与长文本','12 状态与适配','large')
add('82-keyboard','表单与软键盘','12 状态与适配','keyboard')
add('83-nav-transition','圆形扩散 · 中间帧','13 动效分镜','nav-motion')
add('84-reduced-motion','减少动态效果','13 动效分镜','result',note='保留静态勾选、结果文字与进度，不播放扩散、位移或粒子。')

def form(c,s):
    c.header(s['title']);c.title(s['title'], '分组填写，完整保留网页字段',y=104)
    y=180
    if s['group'].startswith('07'):
        c.box(20,178,350,48,'surface',12,'line');c.text('启用此渠道',34,193,13,bold=True);c.box(309,190,43,24,'green',12);c.circle(340,202,9,'surface');y=248
    for label,value in s['data'][:6]:c.field(label,value,y);y+=80
    if s['note'] and y<700:c.note('说明',s['note'],y=min(y+4,660),h=78)
    if s['group'].startswith('07'):
        c.button('测试发送',x=20,w=104,kind='surface');c.button('保存配置',x=136,w=234)
    else:c.button('测试连接' if 'sync-login' in s['id'] else '保存并继续')
    c.box(151,837,88,3,'ink',2)

def rows(c,s):
    c.header(s['title']);c.title(s['title'],s['state'],y=106);y=182
    c.box(20,y,350,min(520,len(s['data'])*74+12),'surface',16,'line')
    for a,b,d in s['data']:c.row(a,b,d,y=y+5);y+=74
    if s['note'] and y<670:c.note('使用说明',s['note'],y=y+20,h=84)
    c.button('完成',kind='action');c.box(151,837,88,3,'ink',2)

def home(c,s):
    c.header(root=True);c.title('总览','11月1日，星期日 · 数据已同步')
    c.box(20,183,350,164,'soft',20);c.text('本月预计支出',38,202,13,'sub');c.text('¥ 286.40',38,230,36,bold=True);c.text('较上月减少 12.8%',39,291,12,'green');c.right('预算 ¥500',352,292,12,'sub')
    c.box(38,325,312,4,'surface',2);c.box(38,325,179,4,'green',2)
    c.box(20,363,350,49,'warm',12);c.text('3 项订阅将在 7 天内到期',36,378,13,'amber',True);c.icon('next',336,377,18,'amber')
    c.text('接下来到期',20,439,16,bold=True);c.right('续费计划 ↗',370,441,12,'green',True)
    c.box(20,475,350,169,'surface',16,'line');c.row('DMIT','东京主机 · 11月8日','38.50 USD',487,logo='D');c.row('iCloud+','家庭存储 · 11月10日','6.00 CNY',561,logo='i')
    c.text('本年度',20,674,12,'sub');c.text('¥ 3,426.80',20,696,24,bold=True);c.right('31 项有效订阅',370,704,12,'sub');c.nav(0)

def subscriptions(c,s):
    c.header(root=True);c.title('订阅','31 项 · 按分类整理');c.circle(345,126,23,'action');c.icon('plus',335,116,20,'on')
    c.box(20,181,350,46,'surface',12,'line');c.icon('search',34,194,18);c.text('搜索服务、备注或号码',62,194,13,'sub')
    for label,x,k in [('全部',20,'soft'),('循环',94,'muted'),('买断',168,'muted')]:c.pill(label,x,244,k,66)
    c.text('VPS / 服务器',20,299,14,bold=True);c.right('3 项',370,300,12,'sub')
    for i,(name,sub,price) in enumerate([('DMIT','东京主机 · 11月8日','38.50 USD'),('BandwagonHost','备用线路 · 12月2日','45.68 USD'),('Colocrossing','实验环境 · 11月26日','15.60 USD')]):c.row(name,sub,price,330+i*87,logo=name)
    c.text('SIM / 保号',20,609,14,bold=True);c.row('VOXI','保号号码 •••• 2841 · 11月25日','0.20 EUR',639,logo='V');c.nav(1)

def detail(c,s):
    c.header('订阅详情');c.logo('D',20,115,54);c.text('DMIT',90,113,24,bold=True);c.text('东京主机 · Premium Tokyo',90,151,12,'sub');c.text('38.50',20,214,38,bold=True);c.text('USD / 月',160,239,14,'sub');c.pill('7 天后续费',20,281,'soft',110)
    c.box(20,337,350,229,'surface',16,'line')
    for i,(a,b) in enumerate([('下次到期','2026-11-08'),('开始日期','2025-11-08'),('支付方式','信用卡 •••• 2841'),('自动续费','已开启')]):c.text(a,36,354+i*52,13,'sub');c.right(b,354,354+i*52,13,bold=True)
    c.text('更多资料',20,599,16,bold=True);c.row('网络与附加信息','IPv4 / IPv6、家庭、网站、备注','查看',625);c.button('编辑',x=20,w=104,kind='surface');c.button('记录续费',x=136,w=234);c.box(151,837,88,3,'ink',2)

def renewal(c,s):
    selected='selected' in s['note'];c.header('续费计划');c.text('RENEWALS',20,108,11,'green',True);c.text('续费计划',20,132,28,bold=True);c.text('6 项待安排 · 未来 30 天',20,177,12,'sub');c.ring(342,151,27,.33 if selected else 0);c.text('2' if selected else '0',335,138,20,bold=True)
    c.text('接下来到期',20,225,16,bold=True);c.pill('30 天',289,219,'muted',81);c.icon('down',346,225,13)
    c.box(20,270,350,204,'surface',20,'line');c.text('2026-11-08',39,288,12,'green');c.right('1 / 6',351,288,12,'sub');c.logo('D',39,326,42);c.text('DMIT',94,324,19,bold=True);c.text('东京主机 · 工作使用',94,354,12,'sub');c.text('38.50',39,405,27,bold=True);c.text('USD',126,421,12,'sub');c.right('查看详情 ↗',351,420,12,'green')
    c.text('选择已续费的订阅',20,504,15,bold=True);c.right('查看全部',352,506,12,'sub');c.icon('down',357,510,13)
    c.box(31,575,328,85,'surface',16,'line');c.box(25,567,340,85,'surface',16,'line');c.box(20,559,350,85,'soft' if selected else 'surface',16,'green' if selected else 'line')
    c.box(34,590,20,20,'green' if selected else 'surface',6,'green' if selected else 'sub')
    if selected:c.icon('check',35,590,18,'on')
    c.logo('D',66,581,32);c.text('DMIT',109,578,14,bold=True);c.text('东京主机',109,606,12,'sub');c.right('38.50',354,580,14,bold=True);c.right('USD',354,608,11,'sub');c.text('选择后核对新的起算方式',20,681,12,'sub')
    if selected:c.box(20,703,350,54,'surface',16,'line');c.text('2 项已选',35,722,13,bold=True);c.button('核对续费',y=706,x=221,w=143)
    c.nav(0)

def sheet(c,s):
    c.header(root=True);c.title('续费计划','6 项待安排 · 保留原页面上下文');c.box(20,184,350,133,'muted',20)
    c.shade();c.box(0,266,390,578,'surface',24);c.box(177,278,36,4,'line',2);c.text(s['title'],22,304,22,bold=True);c.icon('close',341,308,21)
    y=362
    for a,b in s['data'][:5]:
        c.box(20,y,350,67,'bg',12,'line');c.text(a,34,y+12,14,bold=True);c.text(b,34,y+38,12,'sub',maxw=318,lines=1);y+=78
    if s['note'] and y<720:c.text(s['note'],23,y+8,12,'sub',maxw=344,lines=2)
    c.button('确认删除' if 'delete' in s['id'] else '确认并继续',y=771);c.box(151,837,88,3,'ink',2)

def calendar(c,s):
    c.header(root=True);c.title('日历','2026 年 11 月');c.box(20,185,350,336,'surface',20,'line')
    for i,d in enumerate('一二三四五六日'):c.text(d,38+i*47,202,12,'sub')
    for day in range(1,31):
        col=(day+5)%7;row=(day+5)//7;x=44+col*47;y=250+row*43
        if day==15:c.circle(x,y+8,17,'action')
        c.text(str(day),x-7,y-1,13,'on' if day==15 else 'ink',day==15)
        if day in [8,10,15,25,26]:c.circle(x,y+27,2,'green')
    c.text('11月15日 · 3 项',20,552,16,bold=True);c.row('DMIT','东京主机 · 每月续费','38.50 USD',593,logo='D');c.row('iCloud+','家庭存储','6.00 CNY',669,logo='i');c.nav(2)

def reports(c,s):
    c.header(root=True);c.title('报表','2026 年 · 成本估算');c.text('¥ 3,426.80',20,185,34,bold=True);c.text('全年循环订阅预计支出',20,235,12,'sub')
    c.box(20,280,350,209,'surface',20,'line');values=[56,82,64,93,114,96,126,108,142,122,132,102]
    for i,v in enumerate(values):c.box(36+i*26,455-v,13,v,'green' if i==10 else 'soft',4)
    for x,txt in [(35,'1月'),(164,'6月'),(310,'12月')]:c.text(txt,x,466,10,'sub')
    c.text('分类支出',20,520,16,bold=True)
    for i,(name,value,pct) in enumerate([('服务器','¥ 1,482',.74),('软件与 AI','¥ 926',.46),('其他','¥ 1,018',.51)]):c.bar(name,value,pct,558+i*60)
    c.nav(3)

def settings(c,s):
    c.header(root=True);c.title('设置','本地资料与网页账号独立管理');c.box(20,183,350,80,'surface',16,'line');c.logo('E',36,204,36);c.text('demo-account',86,198,15,bold=True);c.text('已连接 · 上次同步 09:41',86,225,12,'green');c.icon('next',338,211)
    for y,label,sub in [(299,'外观与偏好','主题、语言、预算与币种'),(375,'提醒与通知','提醒计划、外部渠道和记录'),(451,'订阅资料','分类、支付方式与捆绑包'),(527,'备份与同步','加密备份、恢复与冲突处理'),(603,'隐私与系统','应用锁、日志和版本信息')]:c.row(label,sub,'›',y)
    c.nav(4)

def render(s):
    c=Canvas('dark' in s['note']);k=s['kind']
    if k=='form':form(c,s)
    elif k=='rows':rows(c,s)
    elif k=='home':home(c,s)
    elif k=='subscriptions':subscriptions(c,s)
    elif k=='detail':detail(c,s)
    elif k=='renewals':renewal(c,s)
    elif k=='sheet':sheet(c,s)
    elif k=='calendar':calendar(c,s)
    elif k=='reports':reports(c,s)
    elif k=='settings':settings(c,s)
    elif k=='services':
        c.header('新增订阅');c.title('先选择服务','从服务库带入图标、分类和官方网站');c.field('搜索服务','输入服务名称或供应商',180)
        for i,(a,b) in enumerate([('DMIT','VPS / 服务器'),('VOXI','SIM / 保号'),('ChatGPT Plus','软件与 AI'),('iCloud+','存储与备份')]):c.row(a,b,'选择',280+i*78,logo=a)
        c.button('手动创建服务',kind='surface')
    elif k=='icons':
        c.header('服务图标');c.title('选择图标','内置图标、手机图片、URL 或 Emoji');c.logo('D',160,181,70)
        for row in range(3):
            for col,label in enumerate(['D','N','V','i','C']):c.logo(label,25+col*72,286+row*68,48)
        for i,label in enumerate(['从手机上传图片','通过 URL 下载','输入 Emoji']):c.row(label,'不超过 2 MB','›',505+i*67)
        c.button('使用此图标')
    elif k in ['stack','expanded','bulk']:
        c.header(s['title']);c.title(s['title'],'明确身份后再批量操作');names=[('DMIT','东京主机','38.50 USD'),('VOXI','保号号码 •••• 2841','0.20 EUR'),('ChatGPT Plus','工作订阅','20.00 USD'),('iCloud+','家庭存储','6.00 CNY')]
        if k=='stack':
            for i in [2,1,0]:c.box(20+i*5,250+i*9,350-i*10,110,'surface',16,'line')
            c.logo('D',36,276,40);c.text('DMIT',90,271,18,bold=True);c.text('东京主机 · 38.50 USD',90,305,12,'sub');c.button('展开全部 6 项',y=401,kind='surface')
        else:
            for i,(a,b,d) in enumerate(names):c.row(a,b,d,215+i*100,logo=a,checked=i<2,h=90)
            c.button('核对所选 2 项' if k=='expanded' else '续费 / 分类 / 启停 / 删除')
    elif k=='timeline':
        c.header('到期时间线');c.title('按日期安排','停稳后更新对应时间线');
        for i,(name,date,amount) in enumerate([('DMIT','11月8日','38.50 USD'),('iCloud+','11月10日','6.00 CNY'),('VOXI','11月25日','0.20 EUR')]):
            yy=216+i*160;c.circle(30,yy+25,4,'green' if i<2 else 'line');
            if i<2:c.line(30,yy+34,30,yy+175,'green' if i==0 else 'line',2)
            c.box(49,yy,321,138,'soft' if i==1 else 'surface',18,'green' if i==1 else 'line');c.text(date,65,yy+14,12,'green');c.text(name,65,yy+43,20,bold=True);c.text(amount,65,yy+88,16,bold=True)
        c.button('↑ 上一项                 下一项 ↓',kind='surface')
    elif k=='wheel':
        sheet(c,dict(s,title='时间范围',data=[],note=''))
        c.text('选择要查看的未来天数',22,362,14,'sub');c.box(105,430,180,54,'soft',12)
        for value,y in [('7 天',393),('14 天',444),('30 天',501),('60 天',558)]:c.text(value,164,y,26,'ink' if y==444 else 'sub',y==444)
        c.circle(55,457,23,'muted');c.text('−',47,443,21);c.circle(335,457,23,'muted');c.text('+',326,443,21);c.text('拖动有惯性，越界后回弹；也可点按选择。',25,644,12,'sub',maxw=335);c.button('使用这个范围',y=771)
    elif k=='feedback':
        sheet(c,dict(s,title='记录续费',data=[('本次所选','2 项 · 核对后才修改日期')],note=''))
        if s['note']=='saving':c.ring(195,535,30,.55);c.text('正在保存…',151,594,16,bold=True);c.text('避免重复操作',153,624,12,'sub');c.button('正在保存…',y=771,kind='muted')
        elif s['note']=='success':
            c.circle(195,537,32,'green');c.icon('check',177,519,36,'on')
            for a in range(0,360,45):r=math.radians(a);c.circle(195+65*math.cos(r),537+65*math.sin(r),2.5,'green')
            c.text('已记录 2 项续费',132,640,18,bold=True);c.text('新的到期日已保存',141,674,12,'sub');c.button('完成',y=771)
        else:c.note('1 项保存失败','成功项目已完成；只重试剩余项目，不重复续费。',475,'rose',110);c.button('重试剩余 1 项',y=771)
    elif k=='bars':
        c.header(s['title']);c.title('分类明细','循环订阅与买断分别计算')
        for i,(a,v,p) in enumerate([('VPS / 服务器','¥ 128.90',.84),('软件与 AI','¥ 92.40',.61),('SIM / 保号','¥ 36.80',.24),('视频与音乐','¥ 28.30',.18)]):c.bar(a,v,p,203+i*90)
        c.note('当前范围','2026年11月 · 可导出 CSV',603);c.button('导出明细',kind='surface')
    elif k=='conflict':
        c.header('同步冲突');c.title('保留正确的版本','双方资料都保留，选择后再同步')
        for y,label,value in [(203,'手机版本','38.50 USD · 东京主机'),(389,'网页版本','42.00 USD · 东京主机 / 升级')]:c.box(20,y,350,160,'surface',16,'line');c.text(label,36,y+17,12,'green');c.text('DMIT',36,y+47,20,bold=True);c.text(value,36,y+92,13,'sub');c.text('更新于今天 '+('09:36' if y==203 else '09:38'),36,y+126,12,'sub')
        c.note('包含通知密钥时','默认隐藏敏感值，选择前可核对字段差异。',579);c.button('采用手机版本',x=20,w=169);c.button('采用网页版本',x=201,w=169,kind='surface')
    elif k=='onboarding':
        c.status();c.box(155,151,80,80,'soft',26);c.icon('check',173,169,44,'green');c.text('把续费安排好',85,285,28,bold=True);c.text('订阅、保号和账目，先保存在你的手机。',41,345,14,'sub',maxw=308);c.note('从本地开始','无需连接网页也能管理订阅；之后可连接账号同步。',444,'surface',109);c.button('开始本地使用',y=687);c.button('连接已有网页账号',y=748,kind='surface')
    elif k in ['empty','loading','offline','error']:
        c.header(root=True);c.title('订阅',{'empty':'还没有添加订阅','loading':'正在读取本地资料','offline':'离线可用 · 等待网络恢复','error':'资料已保留，操作尚未完成'}[k])
        if k=='empty':c.icon('card',170,315,50,'sub');c.text('从第一项订阅开始',96,409,20,bold=True);c.text('选择服务库，或手动添加。',107,454,13,'sub');c.button('添加订阅',y=531)
        elif k=='loading':
            for yy in [210,330,450]:c.box(20,yy,350,99,'surface',16);c.box(36,yy+20,40,40,'muted',12);c.box(91,yy+22,180,12,'muted',5);c.box(91,yy+47,130,10,'muted',5)
            c.text('正在加载，尚未显示为空状态。',89,616,12,'sub')
        elif k=='offline':c.note('离线模式','可继续查看和编辑。2 项待上传，联网后重试。',192,'warm',108);c.row('DMIT','东京主机 · 手机资料已保存','待上传',335,logo='D');c.row('VOXI','保号号码 •••• 2841','已缓存',425,logo='V');c.button('查看同步队列',y=568,kind='surface')
        else:c.note('保存未完成','网络暂不可用。输入内容与待上传队列均已保留。',234,'rose',112);c.button('重试',y=403);c.button('继续本地使用',y=464,kind='surface')
        c.nav(1)
    elif k=='large':
        c.header('放大字号检查');c.text('订阅详情',20,108,31,bold=True);c.text('DMIT · Tokyo Premium',20,174,23,bold=True,maxw=350);c.text('工作主机 / 长备注用于验证自然换行，不以省略号隐藏关键身份。',20,227,19,'sub',maxw=350,lines=4);c.box(20,368,350,150,'surface',16,'line');c.text('38.50 USD',36,395,31,bold=True);c.text('下次到期 2026-11-08',36,455,19,'sub');c.note('135% 字号适配','内容变高，保持 48px 操作目标；不缩放整张页面。',565,'soft',105);c.button('核对续费')
    elif k=='keyboard':
        form(c,dict(s,data=[('服务名称','DMIT'),('个性化备注','东京主机 · 工作使用'),('价格','38.50')],note=''))
        c.box(0,548,390,296,'muted',0);c.button('保存',y=491)
        for row,letters in enumerate(['QWERTYUIOP','ASDFGHJKL','ZXCVBNM']):
            ww=34;off=(390-len(letters)*ww)/2
            for i,ch in enumerate(letters):c.box(off+i*ww,575+row*52,29,43,'surface',6);c.text(ch,off+i*ww+8,589+row*52,13)
        c.box(89,746,211,44,'surface',6);c.text('空格',176,758,12,'sub');c.text('键盘弹出，保存操作保持可见。',93,812,12,'sub')
    elif k=='nav-motion':
        home(c,s);c.circle(117,789,238,'soft');c.text('新页面从触点扩散',27,586,20,'green',True);c.text('半径到达最远角，旧页保留空间连续性。',27,626,12,'sub',maxw=290);c.circle(117,789,6,'green')
    else:
        c.header(s['title']);c.circle(195,300,37,'soft');c.icon('check',174,279,42,'green');c.text('操作完成',143,376,24,bold=True);c.text(s['note'],35,438,15,'sub',maxw=320,lines=5);c.button('返回')
    c.save(s['id']);return c.im

def board(ids,name,title,notes=None,cols=3):
    thumb_w=312;thumb_h=675;gap=28;rows=math.ceil(len(ids)/cols);bw=cols*(thumb_w+gap)+gap;bh=96+rows*(thumb_h+80)
    im=Image.new('RGB',(bw,bh),'#e9ece8');d=ImageDraw.Draw(im);f=ImageFont.truetype(BOLD,26);small=ImageFont.truetype(FONT,14)
    d.text((gap,22),title,font=f,fill=LIGHT['ink']);d.text((gap,61),'EasySub / debug23 · 概念草图，非实际功能完成声明',font=small,fill=LIGHT['sub'])
    for i,slug in enumerate(ids):
        s=next(s for s in SCREENS if s['id']==slug);x=gap+(i%cols)*(thumb_w+gap);y=96+(i//cols)*(thumb_h+80)
        src=Image.open(OUT/'screens'/f'{slug}.png').resize((thumb_w,thumb_h),Image.Resampling.LANCZOS);im.paste(src,(x,y))
        d.text((x,y+thumb_h+10),s['title'][:21],font=small,fill=LIGHT['ink'])
        if notes:d.text((x,y+thumb_h+35),notes[i][:28],font=small,fill=LIGHT['sub'])
    im.save(OUT/'boards'/f'{name}.png')

for s in SCREENS:render(s)
groups=list(dict.fromkeys(s['group'] for s in SCREENS))
for i,g in enumerate(groups):board([s['id'] for s in SCREENS if s['group']==g],f'{i+1:02d}-'+g.split(' ',1)[1],g,cols=3)
board(['01-home','02-subscriptions','03-detail','13-renewals'],'00-main','01 / 核心视觉与信息层级',cols=2)
MOTION=[('completion','完成反馈',['19-renew-confirm','20-renew-saving','21-renew-success'],['核对后提交','保存中，不可重复操作','收缩、对勾、粒子，结果持续保留']),('selection','勾选联动',['13-renewals','14-selected','19-renew-confirm'],['默认状态','进度与计数、背景同步变化','核对具体身份']),('stack','堆叠展开',['15-stack','16-expanded','15-stack'],['卡背叠放，不可误选','按顺序展开','再次收回']),('snap','吸附与描线',['13-renewals','17-timeline','17-timeline'],['开始滑动','中间卡吸附','停稳后描画时间线']),('wheel','惯性滚轮',['13-renewals','18-wheel','14-selected'],['打开范围面板','速度衰减、边界回弹、刻度吸附','更新范围并回到原页面']),('navigation','圆形扩散',['01-home','83-nav-transition','02-subscriptions'],['触点决定圆心','扩散到最远角','新页完全呈现']),('reduced','减少动态效果',['14-selected','84-reduced-motion','21-renew-success'],['保留勾选语义','取消位移与粒子','静态对勾和结果文字'])]
for slug,title,ids,notes in MOTION:board(ids,'motion-'+slug,title+' / 动效分镜',notes)

# All-screen contact sheet, readable details are available in each individual artboard.
tw,th,gap,cols=156,338,20,8;rows=math.ceil(len(SCREENS)/cols);im=Image.new('RGB',(cols*(tw+gap)+gap,100+rows*(th+57)),'#e9ece8');d=ImageDraw.Draw(im)
d.text((20,20),f'EasySub / debug23 全量草图 · {len(SCREENS)} 个页面与状态',font=ImageFont.truetype(BOLD,25),fill=LIGHT['ink'])
d.text((20,61),'所有数据均为演示；暗色、放大字号、异常状态与七项交互分镜包含在内。',font=ImageFont.truetype(FONT,14),fill=LIGHT['sub'])
for i,s in enumerate(SCREENS):
 x=gap+(i%cols)*(tw+gap);y=100+(i//cols)*(th+57);im.paste(Image.open(OUT/'screens'/f'{s["id"]}.png').resize((tw,th),Image.Resampling.LANCZOS),(x,y));d.text((x,y+th+7),s['title'][:11],font=ImageFont.truetype(FONT,12),fill=LIGHT['ink'])
im.save(OUT/'all-screens.png')
(OUT/'manifest.json').write_text(json.dumps(SCREENS,ensure_ascii=False,indent=2),encoding='utf-8')
cards=''.join(f'<article class="artboard" data-group="{s["group"]}" data-title="{s["title"]}"><button class="open" data-id="{s["id"]}" aria-label="查看{s["title"]}"><img loading="lazy" src="screens/{s["id"]}.png" alt="{s["title"]}设计草图" width="390" height="844"/></button><div class="caption"><b>{i+1:02d} / {s["title"]}</b><small>{s["group"]} · {s["state"]}</small><a href="screens/{s["id"]}.svg" target="_blank">SVG</a> <a href="screens/{s["id"]}.png" target="_blank">PNG</a></div></article>' for i,s in enumerate(SCREENS))
html_doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EasySub · 全量设计草图</title><style>
*{box-sizing:border-box}body{margin:0;background:#e9ece8;color:#16191d;font:14px/1.6 'Microsoft YaHei',system-ui,sans-serif}header{padding:40px clamp(20px,5vw,72px) 28px;background:#f6f7f5;border-bottom:1px solid #cfd3d2}.eyebrow{font-size:12px;color:#0f7352;letter-spacing:.15em;font-weight:700}h1{font-size:clamp(26px,4vw,42px);letter-spacing:-.04em;margin:8px 0}header p{max-width:760px;color:#59606a}.tools{display:flex;gap:12px;flex-wrap:wrap;margin-top:24px}input,select,button,a.action{font:inherit;min-height:44px;border:1px solid #cfd3d2;background:white;color:#16191d;border-radius:10px;padding:10px 14px}input{min-width:240px}a{color:#0f7352}button{cursor:pointer}a.action{text-decoration:none}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(255px,1fr));gap:32px;padding:32px clamp(20px,4vw,64px)}.artboard{min-width:0}.open{display:block;padding:0;width:100%;border:0;border-radius:18px;overflow:hidden;background:#f6f7f5;box-shadow:0 8px 24px #16191d12}.open img{width:100%;height:auto;display:block}.caption{padding:14px 4px}.caption b,.caption small{display:block}.caption small{color:#59606a;margin:4px 0}.caption a{margin-right:12px}.motion{padding:24px clamp(20px,4vw,64px);background:#f6f7f5}.motion a{display:inline-block;margin:8px 18px 8px 0}dialog{border:0;border-radius:16px;max-width:min(95vw,700px);max-height:95vh;padding:12px;background:#f6f7f5}dialog::backdrop{background:#101813b8}.viewer-bar{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px}#preview{display:block;max-width:100%;height:auto;max-height:78vh;margin:auto}button:focus-visible,a:focus-visible{outline:3px solid #0f7352;outline-offset:4px}.hint{font-size:12px;color:#59606a}article[hidden]{display:none}@media(min-width:1500px){main{grid-template-columns:repeat(5,minmax(0,1fr))}}@media(prefers-reduced-motion:no-preference){.open:hover{box-shadow:0 10px 28px #16191d25;transition:box-shadow 150ms}}
</style><header><div class="eyebrow">EASYSUB / DESIGN ATLAS / DEBUG23</div><h1>每一笔订阅，都有清楚的安排。</h1><p>全量页面、关键面板、异常状态与交互动效分镜。使用演示数据，设计稿不表示原生通知、设备认证、后台任务等规划功能已经完成。</p><div class="tools"><input id="search" type="search" aria-label="搜索页面" placeholder="搜索页面或功能"><select id="group" aria-label="按模块筛选"><option value="">全部模块</option>GROUPS</select><a class="action" href="all-screens.png" target="_blank">全量总览 PNG</a><a class="action" href="boards/00-main.png" target="_blank">核心视觉板</a><a class="action" href="COVERAGE.md">覆盖清单</a></div><p id="count" class="hint"></p></header><section class="motion"><b>七项交互与流程</b><br>MOTIONS</section><main>CARDS</main><dialog id="viewer"><div class="viewer-bar"><button id="prev" aria-label="上一页">←</button><b id="name"></b><button id="close">关闭</button><button id="next" aria-label="下一页">→</button></div><img id="preview" alt=""><p class="hint">概念草图，非操作真实账号。可用左右方向键翻页，Esc 关闭。</p></dialog><script>
const entries=ENTRIES,viewer=document.querySelector('#viewer');let current=0;function show(i){current=(i+entries.length)%entries.length;const s=entries[current];document.querySelector('#preview').src='screens/'+s.id+'.png';document.querySelector('#preview').alt=s.title+'草图';document.querySelector('#name').textContent=s.title;if(!viewer.open)viewer.showModal()}document.querySelectorAll('.open').forEach(b=>b.onclick=()=>show(entries.findIndex(s=>s.id===b.dataset.id)));document.querySelector('#close').onclick=()=>viewer.close();document.querySelector('#prev').onclick=()=>show(current-1);document.querySelector('#next').onclick=()=>show(current+1);document.addEventListener('keydown',e=>{if(!viewer.open)return;if(e.key==='ArrowRight')show(current+1);if(e.key==='ArrowLeft')show(current-1)});function filter(){const q=document.querySelector('#search').value.toLowerCase(),g=document.querySelector('#group').value;let n=0;document.querySelectorAll('.artboard').forEach(el=>{el.hidden=!(el.dataset.title.toLowerCase().includes(q)&&(!g||el.dataset.group===g));if(!el.hidden)n++});document.querySelector('#count').textContent='显示 '+n+' / '+entries.length+' 个页面与状态'}document.querySelector('#search').oninput=filter;document.querySelector('#group').onchange=filter;filter();
</script></html>'''
html_doc=html_doc.replace('GROUPS',''.join(f'<option>{g}</option>' for g in groups)).replace('MOTIONS',''.join(f'<a href="boards/motion-{slug}.png" target="_blank">{title}</a>' for slug,title,_,_ in MOTION)).replace('CARDS',cards).replace('ENTRIES',json.dumps([dict(id=s['id'],title=s['title']) for s in SCREENS],ensure_ascii=False))
html_doc=html_doc.replace('<a class="action" href="COVERAGE.md">覆盖清单</a>', '<a class="action" href="COVERAGE.md">覆盖清单</a><a class="action" href="FLOWS.md">任务路径</a><a class="action" href="design-system.md">设计规范</a><a class="action" href="design-tokens.css" download>Design tokens</a>')
(OUT/'index.html').write_text(html_doc,encoding='utf-8')
coverage='# debug23 全量草图覆盖清单\n\n共 '+str(len(SCREENS))+' 个页面与状态、七组动效分镜。SVG 可交给设计师编辑，PNG 用于直接评审，index.html 可离线搜索与放大。\n\n所有字段使用演示值；功能规划不代表已实现。全表单分为多个连续页面，避免一张画板塞不下全部字段。\n\n| 模块 | 页面 | 状态/边界 |\n| --- | --- | --- |\n'+''.join(f'| {s["group"]} | {s["title"]} | {s["state"]} |\n' for s in SCREENS)
coverage+='\n## 交付边界\n\n- 视觉方案覆盖 Android 个人功能及网页账号/管理员边界入口，未静默删除网页功能。\n- 全部 14 个外部通知渠道有配置草图；真实发送需要各渠道凭据与网络验证。\n- 原生通知、后台备份、设备认证、正式签名发布等当前 Alpha 未完成项明确保留为规划。\n- 本画册采用 390×844 CSS 设计尺寸，PNG 为 2 倍导出；放大字号与软键盘另设画板，不等同于完成真机适配验收。\n- 动效为前后状态分镜，不是逐帧运行录像；需要后续原型验证中断、惯性和减少动态效果。\n- 图标是统一系统图形与商家首字占位；实际产品接入原有合法商标素材。\n- 画板是设计草图，不会修改真实账号、订阅或密钥。\n'
(OUT/'COVERAGE.md').write_text(coverage,encoding='utf-8')
flows='''# 主要任务路径

- 新增：04 选择服务 → 05 分类库 / 06 图标 → 07 服务价格 → 08 周期日期 → 09 网络共享 → 10 风险卡片 → 11 核对 → 03 详情。
- 续费：13 续费计划 → 18 时间范围 → 14 选择联动 → 19 核对 → 20 保存中 → 21 成功 / 22 部分失败。
- 列表：02 订阅 → 03 详情 / 23 操作菜单 / 25 批量 / 26 排序 / 27 CSV。
- 日历：28 月历 → 29 当日议程 → 03 详情；30 导出 ICS。
- 报表：31 总览 → 32 洞察 / 33 分类 / 34 付款明细。
- 备份：57 备份 → 58 加密导出；59 选择文件 → 60 预览 → 61 方式确认 → 62 结果。
- 同步：63 测试账号 → 64 核对身份 → 65 同步状态 → 66 冲突处理。
- 设置：35 设置 → 36 外观 / 37 提醒 / 38 通知渠道 / 53–56 资料管理 / 57 备份 / 63 同步 / 69–73 系统与网页边界。
- 动效分镜位于 boards/motion-*.png，分别给出起始、中间和结束状态。

所有路径是设计意图。画册支持搜索、分组、放大与翻页，不连接真实账号。
'''
(OUT/'FLOWS.md').write_text(flows,encoding='utf-8')
shutil.copyfile(ROOT/'docs/design-system-debug23.md',OUT/'design-system.md')
shutil.copyfile(ROOT/'frontend/src/android-preview/design-tokens.css',OUT/'design-tokens.css')
(OUT/'README.txt').write_text('打开 index.html 浏览全部草图。screens 包含逐页 SVG/PNG；boards 包含模块总览和七组动效分镜。全部为演示数据，不代表功能已经完成。',encoding='utf-8')
zip_path=OUT.parent/'EasySub-debug23-design-atlas.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(OUT))
print(json.dumps(dict(screens=len(SCREENS),groups=len(groups),motion_boards=len(MOTION),atlas=str(OUT/'index.html'),archive=str(zip_path)),ensure_ascii=False))
