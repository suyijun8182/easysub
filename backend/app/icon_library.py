"""内置常见商家清单：用于服务名联想 + 图标库。

图标按需从公共 favicon 服务下载并缓存到本地 data/icons/library/，
之后由本地静态目录提供，不依赖外网。
"""

# 分类 key -> 显示标签（用于「按分类浏览」服务库）
CATEGORY_LABELS = [
    ("streaming", "流媒体 / Streaming"),
    ("music", "音乐 / Music"),
    ("ai", "AI 服务 / AI"),
    ("gaming", "游戏 / Gaming"),
    ("vps", "VPS / 服务器"),
    ("carrier", "电信运营商 / Carrier"),
    ("cloud", "云存储 / Cloud"),
    ("software", "软件 / Software"),
    ("domain", "域名 / Domain"),
    ("education", "教育 / Education"),
    ("news", "新闻 / News"),
    ("fitness", "健身 / Fitness"),
    ("membership", "会员 / Membership"),
]

# (显示名, 域名, 分类key)
SERVICES = [
    # 流媒体 streaming
    ("Netflix", "netflix.com", "streaming"),
    ("Disney+", "disneyplus.com", "streaming"),
    ("YouTube Premium", "youtube.com", "streaming"),
    ("HBO Max", "max.com", "streaming"),
    ("Prime Video", "primevideo.com", "streaming"),
    ("Hulu", "hulu.com", "streaming"),
    ("Apple TV+", "tv.apple.com", "streaming"),
    ("Paramount+", "paramountplus.com", "streaming"),
    ("Peacock", "peacocktv.com", "streaming"),
    ("Crunchyroll", "crunchyroll.com", "streaming"),
    ("DAZN", "dazn.com", "streaming"),
    ("Viu", "viu.com", "streaming"),
    ("bilibili", "bilibili.com", "streaming"),
    ("爱奇艺 iQIYI", "iqiyi.com", "streaming"),
    ("腾讯视频", "v.qq.com", "streaming"),
    ("优酷 Youku", "youku.com", "streaming"),
    ("芒果TV", "mgtv.com", "streaming"),
    # 音乐 music
    ("Spotify", "spotify.com", "music"),
    ("Apple Music", "music.apple.com", "music"),
    ("YouTube Music", "music.youtube.com", "music"),
    ("Amazon Music", "music.amazon.com", "music"),
    ("Tidal", "tidal.com", "music"),
    ("Deezer", "deezer.com", "music"),
    ("Qobuz", "qobuz.com", "music"),
    ("SoundCloud", "soundcloud.com", "music"),
    ("网易云音乐", "music.163.com", "music"),
    ("QQ音乐", "y.qq.com", "music"),
    # AI
    ("ChatGPT", "openai.com", "ai"),
    ("Claude", "claude.ai", "ai"),
    ("Google Gemini", "gemini.google.com", "ai"),
    ("Perplexity", "perplexity.ai", "ai"),
    ("Midjourney", "midjourney.com", "ai"),
    ("GitHub Copilot", "github.com", "ai"),
    ("Cursor", "cursor.com", "ai"),
    ("Grok", "x.ai", "ai"),
    ("Poe", "poe.com", "ai"),
    ("Mistral AI", "mistral.ai", "ai"),
    ("DeepSeek", "deepseek.com", "ai"),
    ("Suno", "suno.com", "ai"),
    ("ElevenLabs", "elevenlabs.io", "ai"),
    ("Runway", "runwayml.com", "ai"),
    ("文心一言", "yiyan.baidu.com", "ai"),
    ("通义千问", "tongyi.aliyun.com", "ai"),
    ("Kimi", "kimi.moonshot.cn", "ai"),
    # 游戏 gaming
    ("Steam", "steampowered.com", "gaming"),
    ("Epic Games", "epicgames.com", "gaming"),
    ("PlayStation Plus", "playstation.com", "gaming"),
    ("Xbox Game Pass", "xbox.com", "gaming"),
    ("Nintendo Switch Online", "nintendo.com", "gaming"),
    ("EA Play", "ea.com", "gaming"),
    ("Ubisoft+", "ubisoft.com", "gaming"),
    ("GeForce NOW", "nvidia.com", "gaming"),
    ("Apple Arcade", "apple.com", "gaming"),
    # VPS / 云（含主流大厂与 LowEnd 低价商家）
    ("AWS", "aws.amazon.com", "vps"),
    ("Google Cloud", "cloud.google.com", "vps"),
    ("Microsoft Azure", "azure.microsoft.com", "vps"),
    ("Oracle Cloud", "oracle.com", "vps"),
    ("DigitalOcean", "digitalocean.com", "vps"),
    ("Vultr", "vultr.com", "vps"),
    ("Linode / Akamai", "linode.com", "vps"),
    ("Hetzner", "hetzner.com", "vps"),
    ("Contabo", "contabo.com", "vps"),
    ("OVHcloud", "ovhcloud.com", "vps"),
    ("Scaleway", "scaleway.com", "vps"),
    ("UpCloud", "upcloud.com", "vps"),
    ("Gcore", "gcore.com", "vps"),
    ("IONOS", "ionos.com", "vps"),
    ("Kamatera", "kamatera.com", "vps"),
    ("Fly.io", "fly.io", "vps"),
    ("Railway", "railway.app", "vps"),
    ("Render", "render.com", "vps"),
    ("Hostinger", "hostinger.com", "vps"),
    ("Hostwinds", "hostwinds.com", "vps"),
    # LowEnd / 低价 VPS 圈常见商家
    ("DMIT", "dmit.io", "vps"),
    ("RackNerd", "racknerd.com", "vps"),
    ("BandwagonHost 搬瓦工", "bandwagonhost.com", "vps"),
    ("BuyVM / Frantech", "buyvm.net", "vps"),
    ("CloudCone", "cloudcone.com", "vps"),
    ("GreenCloud", "greencloudvps.com", "vps"),
    ("HostHatch", "hosthatch.com", "vps"),
    ("Netcup", "netcup.de", "vps"),
    ("VirMach", "virmach.com", "vps"),
    ("HostDare", "hostdare.com", "vps"),
    ("Hostodo", "hostodo.com", "vps"),
    ("RamNode", "ramnode.com", "vps"),
    ("Spartan Host", "spartanhost.net", "vps"),
    ("AlphaVPS", "alphavps.com", "vps"),
    ("Servarica", "servarica.com", "vps"),
    ("Crunchbits", "crunchbits.com", "vps"),
    ("WebHorizon", "webhorizon.net", "vps"),
    ("Misaka", "misaka.io", "vps"),
    ("ZGOVPS", "zgovps.com", "vps"),
    ("V.PS", "v.ps", "vps"),
    ("LisaHost 丽萨主机", "lisahost.com", "vps"),
    ("Cloudie / 莱卡云", "lcayun.com", "vps"),
    ("雨云 RainYun", "rainyun.com", "vps"),
    ("阿里云", "aliyun.com", "vps"),
    ("腾讯云", "cloud.tencent.com", "vps"),
    ("华为云", "huaweicloud.com", "vps"),
    ("UCloud", "ucloud.cn", "vps"),
    # 电信运营商 carrier
    ("VOXI", "voxi.co.uk", "carrier"),
    ("Vodafone", "vodafone.com", "carrier"),
    ("giffgaff", "giffgaff.com", "carrier"),
    ("EE", "ee.co.uk", "carrier"),
    ("O2", "o2.co.uk", "carrier"),
    ("Three", "three.co.uk", "carrier"),
    ("SMARTY", "smarty.co.uk", "carrier"),
    ("Tesco Mobile", "tescomobile.com", "carrier"),
    ("iD Mobile", "idmobile.co.uk", "carrier"),
    ("1pMobile", "1pmobile.com", "carrier"),
    ("Lebara", "lebara.com", "carrier"),
    ("Lycamobile", "lycamobile.com", "carrier"),
    ("T-Mobile", "t-mobile.com", "carrier"),
    ("AT&T", "att.com", "carrier"),
    ("Verizon", "verizon.com", "carrier"),
    ("Mint Mobile", "mintmobile.com", "carrier"),
    ("Visible", "visible.com", "carrier"),
    ("US Mobile", "usmobile.com", "carrier"),
    ("Ultra Mobile", "ultramobile.com", "carrier"),
    ("Google Fi", "fi.google.com", "carrier"),
    ("中国移动", "10086.cn", "carrier"),
    ("中国联通", "10010.com", "carrier"),
    ("中国电信", "189.cn", "carrier"),
    # 更多运营商 / MVNO（英国）
    ("Sky Mobile", "sky.com", "carrier"),
    ("BT Mobile", "bt.com", "carrier"),
    ("ASDA Mobile", "asdamobile.com", "carrier"),
    ("Talkmobile", "talkmobile.co.uk", "carrier"),
    ("Spusu", "spusu.co.uk", "carrier"),
    ("Superdrug Mobile", "superdrugmobile.com", "carrier"),
    # 美国
    ("Cricket Wireless", "cricketwireless.com", "carrier"),
    ("Boost Mobile", "boostmobile.com", "carrier"),
    ("Metro by T-Mobile", "metrobyt-mobile.com", "carrier"),
    ("Straight Talk", "straighttalk.com", "carrier"),
    ("Tracfone", "tracfone.com", "carrier"),
    ("Consumer Cellular", "consumercellular.com", "carrier"),
    ("Tello Mobile", "tello.com", "carrier"),
    ("Ting Mobile", "ting.com", "carrier"),
    ("Red Pocket Mobile", "redpocket.com", "carrier"),
    ("H2O Wireless", "h2owireless.com", "carrier"),
    # 欧洲
    ("Orange", "orange.fr", "carrier"),
    ("SFR", "sfr.fr", "carrier"),
    ("Free Mobile", "free.fr", "carrier"),
    ("Bouygues Telecom", "bouyguestelecom.fr", "carrier"),
    ("Deutsche Telekom", "telekom.de", "carrier"),
    ("O2 Germany", "o2online.de", "carrier"),
    ("1&1", "1und1.de", "carrier"),
    ("Aldi Talk", "alditalk.de", "carrier"),
    ("congstar", "congstar.de", "carrier"),
    ("TIM", "tim.it", "carrier"),
    ("WindTre", "windtre.it", "carrier"),
    ("Iliad", "iliad.it", "carrier"),
    ("Movistar", "movistar.es", "carrier"),
    # 日韩
    ("NTT Docomo", "docomo.ne.jp", "carrier"),
    ("au by KDDI", "au.com", "carrier"),
    ("SoftBank", "softbank.jp", "carrier"),
    ("Rakuten Mobile", "mobile.rakuten.co.jp", "carrier"),
    ("SK Telecom", "tworld.co.kr", "carrier"),
    ("KT", "kt.com", "carrier"),
    ("LG U+", "lguplus.com", "carrier"),
    # 港澳台 / 东南亚
    ("Singtel", "singtel.com", "carrier"),
    ("StarHub", "starhub.com", "carrier"),
    ("M1", "m1.com.sg", "carrier"),
    ("Circles.Life", "circles.life", "carrier"),
    ("3 Hong Kong", "three.com.hk", "carrier"),
    ("csl", "hkcsl.com", "carrier"),
    ("SmarTone", "smartone.com", "carrier"),
    ("中華電信 Chunghwa", "cht.com.tw", "carrier"),
    ("台灣大哥大 Taiwan Mobile", "taiwanmobile.com", "carrier"),
    # 南亚 / 大洋洲 / 加拿大
    ("Airtel", "airtel.in", "carrier"),
    ("Jio", "jio.com", "carrier"),
    ("Vi (Vodafone Idea)", "myvi.in", "carrier"),
    ("Telstra", "telstra.com.au", "carrier"),
    ("Optus", "optus.com.au", "carrier"),
    ("Rogers", "rogers.com", "carrier"),
    ("Bell", "bell.ca", "carrier"),
    ("Telus", "telus.com", "carrier"),
    ("Fido", "fido.ca", "carrier"),
    ("Koodo Mobile", "koodomobile.com", "carrier"),
    # eSIM / 旅行流量
    ("Airalo", "airalo.com", "carrier"),
    ("Holafly", "holafly.com", "carrier"),
    ("Nomad eSIM", "getnomad.app", "carrier"),
    ("Ubigi", "ubigi.com", "carrier"),
    ("Saily", "saily.com", "carrier"),
    # 云存储 cloud
    ("Google One", "one.google.com", "cloud"),
    ("iCloud+", "icloud.com", "cloud"),
    ("Dropbox", "dropbox.com", "cloud"),
    ("OneDrive", "onedrive.live.com", "cloud"),
    ("MEGA", "mega.nz", "cloud"),
    ("pCloud", "pcloud.com", "cloud"),
    ("Backblaze", "backblaze.com", "cloud"),
    ("Box", "box.com", "cloud"),
    ("百度网盘", "pan.baidu.com", "cloud"),
    # 软件 software
    ("Microsoft 365", "microsoft.com", "software"),
    ("Adobe Creative Cloud", "adobe.com", "software"),
    ("Notion", "notion.so", "software"),
    ("1Password", "1password.com", "software"),
    ("Bitwarden", "bitwarden.com", "software"),
    ("JetBrains", "jetbrains.com", "software"),
    ("Figma", "figma.com", "software"),
    ("Canva", "canva.com", "software"),
    ("Grammarly", "grammarly.com", "software"),
    ("Zoom", "zoom.us", "software"),
    ("Setapp", "setapp.com", "software"),
    ("Todoist", "todoist.com", "software"),
    # 域名 domain
    ("Cloudflare", "cloudflare.com", "domain"),
    ("Namecheap", "namecheap.com", "domain"),
    ("GoDaddy", "godaddy.com", "domain"),
    ("Porkbun", "porkbun.com", "domain"),
    ("Dynadot", "dynadot.com", "domain"),
    ("Gandi", "gandi.net", "domain"),
    # 教育 education
    ("Coursera", "coursera.org", "education"),
    ("Udemy", "udemy.com", "education"),
    ("Duolingo", "duolingo.com", "education"),
    ("MasterClass", "masterclass.com", "education"),
    ("Skillshare", "skillshare.com", "education"),
    ("Brilliant", "brilliant.org", "education"),
    ("LinkedIn Learning", "linkedin.com", "education"),
    # 新闻 news
    ("Medium", "medium.com", "news"),
    ("The New York Times", "nytimes.com", "news"),
    ("The Wall Street Journal", "wsj.com", "news"),
    ("The Economist", "economist.com", "news"),
    ("Bloomberg", "bloomberg.com", "news"),
    # 健身 fitness
    ("Strava", "strava.com", "fitness"),
    ("Peloton", "onepeloton.com", "fitness"),
    ("MyFitnessPal", "myfitnesspal.com", "fitness"),
    ("Whoop", "whoop.com", "fitness"),
    # 会员 membership
    ("Amazon Prime", "amazon.com", "membership"),
    ("Costco", "costco.com", "membership"),
    ("Patreon", "patreon.com", "membership"),
    ("Sam's Club", "samsclub.com", "membership"),

    # ===== 补充：各分类更多常用服务 =====
    # 流媒体
    ("ESPN+", "espn.com", "streaming"),
    ("Discovery+", "discoveryplus.com", "streaming"),
    ("MUBI", "mubi.com", "streaming"),
    ("BritBox", "britbox.com", "streaming"),
    ("Starz", "starz.com", "streaming"),
    ("Showtime", "showtime.com", "streaming"),
    ("fuboTV", "fubo.tv", "streaming"),
    ("Sling TV", "sling.com", "streaming"),
    ("Plex", "plex.tv", "streaming"),
    ("Twitch", "twitch.tv", "streaming"),
    ("Rakuten Viki", "viki.com", "streaming"),
    ("WeTV", "wetv.vip", "streaming"),
    ("iQIYI International", "iq.com", "streaming"),
    ("Hotstar / JioHotstar", "hotstar.com", "streaming"),
    ("ABEMA", "abema.tv", "streaming"),
    ("U-NEXT", "unext.jp", "streaming"),
    # 音乐
    ("Pandora", "pandora.com", "music"),
    ("iHeartRadio", "iheart.com", "music"),
    ("KKBOX", "kkbox.com", "music"),
    ("酷狗音乐", "kugou.com", "music"),
    ("酷我音乐", "kuwo.cn", "music"),
    ("咪咕音乐", "music.migu.cn", "music"),
    # AI
    ("Character.AI", "character.ai", "ai"),
    ("You.com", "you.com", "ai"),
    ("Jasper", "jasper.ai", "ai"),
    ("Leonardo.ai", "leonardo.ai", "ai"),
    ("Ideogram", "ideogram.ai", "ai"),
    ("HeyGen", "heygen.com", "ai"),
    ("Descript", "descript.com", "ai"),
    ("Luma AI", "lumalabs.ai", "ai"),
    ("NotebookLM", "notebooklm.google.com", "ai"),
    ("智谱清言 GLM", "chatglm.cn", "ai"),
    ("豆包 Doubao", "doubao.com", "ai"),
    ("腾讯元宝", "yuanbao.tencent.com", "ai"),
    # 游戏
    ("Humble Bundle", "humblebundle.com", "gaming"),
    ("Discord Nitro", "discord.com", "gaming"),
    ("Roblox Premium", "roblox.com", "gaming"),
    ("Riot Games", "riotgames.com", "gaming"),
    ("Minecraft", "minecraft.net", "gaming"),
    ("World of Warcraft", "worldofwarcraft.com", "gaming"),
    ("Final Fantasy XIV", "finalfantasyxiv.com", "gaming"),
    ("HoYoverse 米哈游", "hoyoverse.com", "gaming"),
    ("Amazon Luna", "luna.amazon.com", "gaming"),
    # VPS / 主机
    ("Servers.com", "servers.com", "vps"),
    ("InterServer", "interserver.net", "vps"),
    ("A2 Hosting", "a2hosting.com", "vps"),
    ("GreenGeeks", "greengeeks.com", "vps"),
    ("Time4VPS", "time4vps.com", "vps"),
    ("Aeza", "aeza.net", "vps"),
    ("PQ.Hosting", "pq.hosting", "vps"),
    ("Nexus Bytes", "nexusbytes.com", "vps"),
    ("Advin Servers", "advinservers.com", "vps"),
    ("HostBrr", "hostbrr.com", "vps"),
    ("QuadraNet", "quadranet.com", "vps"),
    ("BuyVM Frantech", "frantech.ca", "vps"),
    # 云存储
    ("Proton Drive", "proton.me", "cloud"),
    ("Sync.com", "sync.com", "cloud"),
    ("Koofr", "koofr.net", "cloud"),
    ("Icedrive", "icedrive.net", "cloud"),
    ("Filen", "filen.io", "cloud"),
    ("Jottacloud", "jottacloud.com", "cloud"),
    ("阿里云盘", "alipan.com", "cloud"),
    ("腾讯微云", "weiyun.com", "cloud"),
    ("115网盘", "115.com", "cloud"),
    ("天翼云盘", "cloud.189.cn", "cloud"),
    # 软件 / 工具 / VPN
    ("Obsidian", "obsidian.md", "software"),
    ("Raycast", "raycast.com", "software"),
    ("Parallels", "parallels.com", "software"),
    ("CleanMyMac", "cleanmymac.com", "software"),
    ("Tailscale", "tailscale.com", "software"),
    ("NordVPN", "nordvpn.com", "software"),
    ("ExpressVPN", "expressvpn.com", "software"),
    ("Surfshark", "surfshark.com", "software"),
    ("Proton VPN", "protonvpn.com", "software"),
    ("Mullvad VPN", "mullvad.net", "software"),
    ("Dashlane", "dashlane.com", "software"),
    ("Airtable", "airtable.com", "software"),
    ("ClickUp", "clickup.com", "software"),
    ("Linear", "linear.app", "software"),
    ("Slack", "slack.com", "software"),
    ("Trello", "trello.com", "software"),
    ("Evernote", "evernote.com", "software"),
    ("DeepL", "deepl.com", "software"),
    # 域名
    ("Name.com", "name.com", "domain"),
    ("Hover", "hover.com", "domain"),
    ("NameSilo", "namesilo.com", "domain"),
    ("Spaceship", "spaceship.com", "domain"),
    ("Squarespace Domains", "domains.squarespace.com", "domain"),
    ("阿里云 / 万网", "wanwang.aliyun.com", "domain"),
    ("DNSPod / 腾讯云", "dnspod.cn", "domain"),
    ("西部数码 West.cn", "west.cn", "domain"),
    # 教育
    ("Khan Academy", "khanacademy.org", "education"),
    ("edX", "edx.org", "education"),
    ("Pluralsight", "pluralsight.com", "education"),
    ("Codecademy", "codecademy.com", "education"),
    ("DataCamp", "datacamp.com", "education"),
    ("Babbel", "babbel.com", "education"),
    ("Busuu", "busuu.com", "education"),
    ("Quizlet", "quizlet.com", "education"),
    ("得到", "dedao.cn", "education"),
    ("网易云课堂", "study.163.com", "education"),
    # 新闻
    ("The Washington Post", "washingtonpost.com", "news"),
    ("The Guardian", "theguardian.com", "news"),
    ("Financial Times", "ft.com", "news"),
    ("The Atlantic", "theatlantic.com", "news"),
    ("Reuters", "reuters.com", "news"),
    ("The New Yorker", "newyorker.com", "news"),
    ("Wired", "wired.com", "news"),
    ("Substack", "substack.com", "news"),
    ("财新 Caixin", "caixin.com", "news"),
    # 健身 / 健康
    ("Nike Training Club", "nike.com", "fitness"),
    ("Calm", "calm.com", "fitness"),
    ("Headspace", "headspace.com", "fitness"),
    ("Fitbit Premium", "fitbit.com", "fitness"),
    ("Garmin Connect+", "garmin.com", "fitness"),
    ("Zwift", "zwift.com", "fitness"),
    ("Freeletics", "freeletics.com", "fitness"),
    ("Keep", "gotokeep.com", "fitness"),
    # 会员 / 权益
    ("Walmart+", "walmart.com", "membership"),
    ("Instacart+", "instacart.com", "membership"),
    ("DoorDash DashPass", "doordash.com", "membership"),
    ("Uber One", "uber.com", "membership"),
    ("京东 PLUS", "jd.com", "membership"),
    ("淘宝 88VIP", "taobao.com", "membership"),
    ("美团会员", "meituan.com", "membership"),
    ("知乎盐选", "zhihu.com", "membership"),
]


def _slug(domain: str) -> str:
    return domain.replace(".", "_").replace("/", "_")


_CAT_LABEL_MAP = dict(CATEGORY_LABELS)


def categories() -> list[dict]:
    """返回服务库分类清单（用于「按分类浏览」服务）。"""
    return [{"key": k, "label": v} for k, v in CATEGORY_LABELS]


def manifest() -> list[dict]:
    """返回图标库清单（含本地图标访问路径与官方网站）。"""
    out = []
    for name, domain, cat in SERVICES:
        slug = _slug(domain)
        out.append(
            {
                "name": name,
                "domain": domain,
                "website": f"https://{domain}",
                "category": cat,
                "category_label": _CAT_LABEL_MAP.get(cat, cat),
                "slug": slug,
                # 前端通过该地址取图标（首次访问会触发本地缓存）
                "icon": f"/api/icons/library/{slug}.png",
            }
        )
    return out


def website_for_name(name: str) -> str | None:
    """按服务名（精确/包含）匹配官方网站，用于创建订阅时自动补全。"""
    if not name:
        return None
    q = name.strip().lower()
    for n, domain, _ in SERVICES:
        if n.lower() == q:
            return f"https://{domain}"
    for n, domain, _ in SERVICES:
        if q and (q in n.lower() or n.lower() in q):
            return f"https://{domain}"
    return None


def domain_for_slug(slug: str) -> str | None:
    target = slug.replace(".png", "")
    for _, domain, _ in SERVICES:
        if _slug(domain) == target:
            return domain
    return None
