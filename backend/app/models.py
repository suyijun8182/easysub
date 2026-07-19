from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 注册审核流程
    email_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    email_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    email_code_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 偏好
    locale: Mapped[str] = mapped_column(String(8), default="zh")        # zh | en | ru
    theme: Mapped[str] = mapped_column(String(32), default="light")
    base_currency: Mapped[str] = mapped_column(String(8), default="CNY")
    # 订阅管理页的分类显示顺序（分类 id 列表，按用户拖拽保存）
    category_order: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Telegram 通知设置（网页可配）
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_bot_token: Mapped[str | None] = mapped_column(String(128), nullable=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telegram_admin_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telegram_api_base: Mapped[str | None] = mapped_column(String(255), nullable=True)  # TG API 反代
    telegram_proxy: Mapped[str | None] = mapped_column(String(255), nullable=True)      # HTTP 代理

    # 多渠道通知配置（飞书 / QQ / Bark / Email / Pushplus / Webhook + Telegram）
    notify_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    icon: Mapped[str | None] = mapped_column(String(128), nullable=True)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    icon: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)


class Currency(Base):
    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    symbol: Mapped[str] = mapped_column(String(8), default="")
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (UniqueConstraint("base", "quote", name="uq_base_quote"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base: Mapped[str] = mapped_column(String(8), index=True)
    quote: Mapped[str] = mapped_column(String(8), index=True)
    rate: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    name: Mapped[str] = mapped_column(String(128))
    plan: Mapped[str | None] = mapped_column(String(128), nullable=True)   # 套餐：高级版/专业版等
    icon: Mapped[str | None] = mapped_column(String(512), nullable=True)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)  # 个性化备注（卡片上展示）
    ipv4: Mapped[str | None] = mapped_column(String(64), nullable=True)     # VPS：IPv4 地址
    ipv6: Mapped[str | None] = mapped_column(String(64), nullable=True)     # VPS：IPv6 地址

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    payment_method_id: Mapped[int | None] = mapped_column(
        ForeignKey("payment_methods.id"), nullable=True
    )
    bundle_id: Mapped[int | None] = mapped_column(ForeignKey("bundles.id"), nullable=True)

    amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")

    # recurring=周期订阅, one_time=一次性买断（永久购买）
    billing_type: Mapped[str] = mapped_column(String(16), default="recurring")
    cycle: Mapped[str] = mapped_column(String(16), default="month")   # day|week|month|year
    cycle_count: Mapped[int] = mapped_column(Integer, default=1)

    start_date: Mapped[date] = mapped_column(Date, default=date.today)
    next_renewal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_renewed_at: Mapped[date | None] = mapped_column(Date, nullable=True)   # 最近付款/续费日

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    show_in_calendar: Mapped[bool] = mapped_column(Boolean, default=True)   # 与日历互动
    sort: Mapped[int] = mapped_column(Integer, default=0)   # 同分类内的拖拽排序

    # 家庭共享成员（JSON 数组，如 ["爸爸","妈妈"]）
    family_members: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # 提醒：提前 N 天（逗号分隔，如 "7,1"）
    remind_days_before: Mapped[str] = mapped_column(String(64), default="7,1")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    category: Mapped["Category | None"] = relationship()
    payment_method: Mapped["PaymentMethod | None"] = relationship()


class Bundle(Base):
    __tablename__ = "bundles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    level: Mapped[str] = mapped_column(String(16), default="info")   # info | warn | error
    action: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    days_before: Mapped[int] = mapped_column(Integer)
    channel: Mapped[str] = mapped_column(String(16), default="telegram")
    status: Mapped[str] = mapped_column(String(16))         # sent | failed
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
