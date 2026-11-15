"""首次启动时写入系统预置数据：货币、分类、付款方式、管理员账户。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Category, Currency, PaymentMethod, User
from app.security import hash_password

# 全球常用流通货币
CURRENCIES = [
    ("USD", "美元 US Dollar", "$"),
    ("CNY", "人民币 Chinese Yuan", "¥"),
    ("EUR", "欧元 Euro", "€"),
    ("GBP", "英镑 British Pound", "£"),
    ("JPY", "日元 Japanese Yen", "¥"),
    ("RUB", "卢布 Russian Ruble", "₽"),
    ("HKD", "港币 Hong Kong Dollar", "HK$"),
    ("TWD", "新台币 Taiwan Dollar", "NT$"),
    ("KRW", "韩元 Korean Won", "₩"),
    ("SGD", "新加坡元 Singapore Dollar", "S$"),
    ("AUD", "澳元 Australian Dollar", "A$"),
    ("CAD", "加元 Canadian Dollar", "C$"),
    ("CHF", "瑞士法郎 Swiss Franc", "Fr"),
    ("INR", "印度卢比 Indian Rupee", "₹"),
    ("BRL", "巴西雷亚尔 Brazilian Real", "R$"),
    ("THB", "泰铢 Thai Baht", "฿"),
    ("MYR", "马来西亚林吉特 Malaysian Ringgit", "RM"),
    ("PHP", "菲律宾比索 Philippine Peso", "₱"),
    ("IDR", "印尼盾 Indonesian Rupiah", "Rp"),
    ("TRY", "土耳其里拉 Turkish Lira", "₺"),
    ("AED", "阿联酋迪拉姆 UAE Dirham", "د.إ"),
]

# 订阅分类（流媒体 / AI / 游戏 / VPS 等）
CATEGORIES = [
    ("流媒体 / Streaming", "📺", "#e50914"),
    ("AI 服务 / AI", "🤖", "#10a37f"),
    ("游戏 / Gaming", "🎮", "#107c10"),
    ("VPS / 服务器", "🖥️", "#0078d4"),
    ("电信运营商 / Carrier (SIM 保号)", "📱", "#e60000"),
    ("软件 / Software", "🧩", "#5b6ee1"),
    ("音乐 / Music", "🎵", "#1db954"),
    ("云存储 / Cloud", "☁️", "#4285f4"),
    ("域名 / Domain", "🌐", "#f59e0b"),
    ("会员 / Membership", "💳", "#9333ea"),
    ("教育 / Education", "📚", "#0ea5e9"),
    ("新闻 / News", "📰", "#374151"),
    ("健身 / Fitness", "💪", "#ef4444"),
    ("其它 / Other", "📦", "#6b7280"),
]

# 付款方式
PAYMENT_METHODS = [
    ("信用卡 / Credit Card", "💳"),
    ("借记卡 / Debit Card", "🏦"),
    ("Apple Pay", "🍎"),
    ("Google Pay", "🅖"),
    ("支付宝 / Alipay", "🅰️"),
    ("微信支付 / WeChat Pay", "💬"),
    ("PayPal", "🅿️"),
    ("银行转账 / Bank Transfer", "🏛️"),
    ("加密货币 / Crypto", "₿"),
]


def seed_all(db: Session) -> None:
    if not db.scalar(select(Currency).limit(1)):
        for code, name, symbol in CURRENCIES:
            db.add(Currency(code=code, name=name, symbol=symbol, is_custom=False))

    if not db.scalar(select(Category).where(Category.is_system.is_(True)).limit(1)):
        for i, (name, icon, color) in enumerate(CATEGORIES):
            db.add(Category(name=name, icon=icon, color=color, is_system=True, sort=i))

    if not db.scalar(select(PaymentMethod).where(PaymentMethod.is_system.is_(True)).limit(1)):
        for name, icon in PAYMENT_METHODS:
            db.add(PaymentMethod(name=name, icon=icon, is_system=True))

    # 首个管理员
    if settings.admin_username and settings.admin_password and settings.admin_password != "admin123":
        exists = db.scalar(select(User).where(User.username == settings.admin_username))
        if not exists:
            db.add(
                User(
                    username=settings.admin_username,
                    email=settings.admin_email,
                    password_hash=hash_password(settings.admin_password),
                    is_admin=True,
                )
            )

    db.commit()
