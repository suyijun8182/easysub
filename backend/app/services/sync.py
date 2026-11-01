"""Account-isolated version journal. Business rows and journal commit together."""
import hashlib
import json
import math
import re
from datetime import date, datetime
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, event, inspect, or_, select
from sqlalchemy.orm import Session

from app import crypto
from app.config import settings
from app.models import (Bundle, Category, Currency, ExchangeRate, NotificationLog,
                        PaymentMethod, Subscription, SyncChange, SyncReceipt, SyncRecord, SyncState, User)
from app.schemas import CategoryIn, PaymentMethodIn, BundleIn, CurrencyIn, SubscriptionIn
from app.services import notify

MODELS = {"categories": Category, "payment-methods": PaymentMethod, "bundles": Bundle,
          "currencies": Currency, "subscriptions": Subscription}
RELATIONS = {"category_id": "categories", "payment_method_id": "payment-methods", "bundle_id": "bundles"}
PREFERENCES = {"base_currency", "monthly_budget", "notify_settings", "category_order"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def encode(value):
    return crypto.encrypt(canonical(value))


def decode(value):
    plaintext = crypto.decrypt(value)
    if not plaintext:
        raise HTTPException(503, {"code": "SYNC_KEY_UNAVAILABLE", "message": "同步数据无法解密，请检查服务器密钥"})
    return json.loads(plaintext)


def lock_account(db, user_id):
    held = db.info.setdefault("sync_locked", set())
    if user_id in held:
        return db.get(User, user_id)
    with db.no_autoflush:
        user = db.scalar(select(User).where(User.id == user_id).with_for_update().execution_options(populate_existing=True))
    if not user:
        raise HTTPException(404, "用户不存在")
    held.add(user_id)
    db.info.setdefault("sync_users", set()).add(user_id)
    return user


def _state(db, user_id):
    state = db.get(SyncState, user_id)
    if state is None:
        state = SyncState(user_id=user_id, epoch=str(uuid4()), cursor=0)
        db.add(state)
        db.flush()
    return state


def _rows(db, user_id):
    rows = {}
    for kind, model in MODELS.items():
        condition = model.user_id == user_id
        if kind in ("categories", "payment-methods"):
            condition = or_(condition, model.is_system.is_(True))
        if kind == "currencies":
            condition = or_(condition, model.is_custom.is_(False))
        rows[kind] = db.scalars(select(model).where(condition).execution_options(populate_existing=True)).all()
    return rows


def _pk(row):
    return str(row.code if isinstance(row, Currency) else row.id)


def _payload(row):
    output = {}
    for column in inspect(type(row)).columns:
        if column.key in ("id", "user_id"):
            continue
        value = getattr(row, column.key)
        output[column.key] = value.isoformat() if isinstance(value, (date, datetime)) else value
    return output


def _notify_config(user):
    # The legacy helper returns empty strings after key rotation; that is not a deletion.
    for channel, fields in notify._SECRET_FIELDS.items():
        for field in fields:
            value = (user.notify_config or {}).get(channel, {}).get(field)
            if isinstance(value, str) and value.startswith("enc:") and not crypto.decrypt(value):
                raise HTTPException(503, {"code": "SYNC_KEY_UNAVAILABLE", "message": "通知密钥无法解密，未同步为空值"})
    return notify.load_config(user)


def capture(db, user_id):
    """Reconcile after flush, including bulk SQL that bypasses ORM dirty events."""
    user = lock_account(db, user_id)
    db.flush()
    if db.get(User, user_id) is None:
        return
    state = _state(db, user_id)
    current = _rows(db, user_id)
    records = db.scalars(select(SyncRecord).where(SyncRecord.user_id == user_id)).all()
    active = {(r.kind, r.entity_pk): r for r in records if not r.deleted}
    seen = set()
    for kind, rows in current.items():
        for row in rows:
            key = (kind, _pk(row))
            seen.add(key)
            if key not in active:
                record = SyncRecord(id=str(uuid4()), user_id=user_id, kind=kind, entity_pk=key[1], version=0, seq=0,
                                    deleted=False, readonly=(getattr(row, "is_system", False) or (isinstance(row, Currency) and not row.is_custom)), fingerprint="", payload=encode({}))
                db.add(record)
                active[key] = record
    for kind in ("preferences", "notification-config"):
        key = (kind, str(user_id)); seen.add(key)
        if key not in active:
            record = SyncRecord(id=str(uuid4()), user_id=user_id, kind=kind, entity_pk=str(user_id), version=0, seq=0,
                                deleted=False, readonly=False, fingerprint="", payload=encode({}))
            db.add(record); active[key] = record
    db.flush()

    def publish(record, data, deleted=False):
        digest = fingerprint({"deleted": deleted, "data": data})
        if digest == record.fingerprint:
            return
        state.cursor += 1
        record.version += 1; record.seq = state.cursor; record.deleted = deleted
        record.fingerprint = digest; record.payload = encode(data)
        db.add(SyncChange(user_id=user_id, seq=state.cursor, record_id=record.id, kind=record.kind,
                          version=record.version, deleted=deleted, readonly=record.readonly, payload=record.payload))

    for kind, rows in current.items():
        for row in rows:
            data = _payload(row)
            if kind == "subscriptions":
                for field, target in RELATIONS.items():
                    data[field] = active[(target, str(getattr(row, field)))].id if getattr(row, field) is not None and (target, str(getattr(row, field))) in active else None
            elif kind == "currencies":
                rate = db.scalar(select(ExchangeRate).where(ExchangeRate.base == settings.exchange_api_base.upper(), ExchangeRate.quote == row.code))
                data.update(rate_base=settings.exchange_api_base.upper(), rate_to_base=rate.rate if rate else (1 if row.code == settings.exchange_api_base.upper() else None))
            publish(active[(kind, _pk(row))], data)
    prefs = {key: getattr(user, key) for key in PREFERENCES}
    prefs["category_order"] = [active[("categories", str(i))].id for i in user.category_order or [] if ("categories", str(i)) in active]
    publish(active[("preferences", str(user_id))], prefs)
    publish(active[("notification-config", str(user_id))], _notify_config(user))
    for key, record in active.items():
        if key not in seen:
            publish(record, decode(record.payload), True)
            record.entity_pk = None  # PK reuse must create a new sync identity.
    db.flush()
    return state


@event.listens_for(Session, "before_commit")
def _capture_committed_writes(db):
    if db.info.get("sync_capturing") or db.in_nested_transaction():
        return
    db.info["sync_capturing"] = True
    try:
        db.flush()
        for user_id in sorted(db.info.get("sync_users", ())):
            if db.get(User, user_id) is not None:
                capture(db, user_id)
    finally:
        db.info["sync_capturing"] = False


@event.listens_for(Session, "after_transaction_end")
def _clear_locks(db, transaction):
    if transaction.parent is None:
        db.info.pop("sync_locked", None)


def envelope(record):
    return {"id": record.id if isinstance(record, SyncRecord) else record.record_id, "kind": record.kind,
            "version": record.version, "seq": record.seq, "deleted": record.deleted,
            "readonly": record.readonly, "data": decode(record.payload)}


class SyncedSubscription(SubscriptionIn):
    model_config = ConfigDict(extra="forbid")
    last_renewed_at: date | None = None
    created_at: datetime | None = None
    sort: int = 0


def _relation(db, user_id, kind, identity):
    if identity is None:
        return None
    record = db.get(SyncRecord, identity) if isinstance(identity, str) else None
    if not record or record.user_id != user_id or record.kind != kind or record.deleted:
        raise ValueError("Invalid relation")
    return int(record.entity_pk)


def apply_operation(db, user, operation):
    kind, identity = operation.kind, str(operation.id)
    record = db.get(SyncRecord, identity)
    if record and (record.user_id != user.id or record.kind != kind):
        return {"op_id": operation.op_id, "status": "rejected", "code": "FORBIDDEN_RECORD"}
    if record and record.readonly:
        return {"op_id": operation.op_id, "status": "rejected", "code": "READONLY_RECORD"}
    if (record.version if record else 0) != operation.base_version:
        return {"op_id": operation.op_id, "status": "conflict", "server": envelope(record) if record else None}
    if record and record.deleted and not operation.deleted and not operation.restore:
        return {"op_id": operation.op_id, "status": "conflict", "server": envelope(record)}
    if operation.deleted:
        if kind not in MODELS:
            raise ValueError("Settings cannot be deleted")
        if record and not record.deleted:
            model = MODELS[kind]
            row = db.get(model, record.entity_pk if kind == "currencies" else int(record.entity_pk))
            if row:
                if kind == "subscriptions":
                    db.execute(delete(NotificationLog).where(NotificationLog.subscription_id == row.id, NotificationLog.user_id == user.id))
                for field, target in RELATIONS.items():
                    if target == kind:
                        for sub in db.scalars(select(Subscription).where(Subscription.user_id == user.id, getattr(Subscription, field) == row.id)).all():
                            setattr(sub, field, None)
                if kind == "currencies" and (user.base_currency == row.code or db.scalar(select(Subscription.id).where(Subscription.user_id == user.id, Subscription.currency == row.code).limit(1))):
                    raise ValueError("Currency in use")
                db.delete(row)
    elif kind in ("preferences", "notification-config"):
        if not record or record.deleted:
            raise ValueError("Settings identity must come from this account")
        data = operation.data
        if kind == "preferences":
            if set(data) - PREFERENCES:
                raise ValueError("Protected preference")
            for key, value in data.items():
                if key == "category_order":
                    value = [_relation(db, user.id, "categories", v) for v in value or []]
                elif key == "base_currency":
                    row = db.get(Currency, value)
                    if not row or (row.is_custom and row.user_id != user.id):
                        raise ValueError("Invalid currency")
                elif key == "monthly_budget" and value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
                    raise ValueError("Invalid budget")
                elif key == "notify_settings" and value is not None and not isinstance(value, dict):
                    raise ValueError("Invalid reminder settings")
                setattr(user, key, value)
        else:
            if set(data) - set(notify.CHANNELS) or any(not isinstance(v, dict) for v in data.values()):
                raise ValueError("Invalid notification config")
            notify.apply_config(user, data)
    else:
        model = MODELS[kind]
        data = dict(operation.data)
        data.pop("is_system", None); data.pop("is_custom", None)
        row = db.get(model, record.entity_pk if kind == "currencies" else int(record.entity_pk)) if record and not record.deleted else None
        if row and row.user_id != user.id:
            raise ValueError("Wrong owner")
        if kind == "subscriptions":
            for field, target in RELATIONS.items():
                if field in data:
                    data[field] = _relation(db, user.id, target, data[field])
            data = SyncedSubscription.model_validate(data).model_dump()
            if not data["name"].strip() or not math.isfinite(data["amount"]) or data["amount"] < 0 or data["cycle_count"] < 1 or data["cycle"] not in {"day", "week", "month", "year"} or data["billing_type"] not in {"recurring", "one_time"}:
                raise ValueError("Invalid subscription")
            currency = db.get(Currency, data["currency"])
            if currency and currency.is_custom and currency.user_id != user.id:
                raise ValueError("Wrong currency owner")
            data["start_date"] = data["start_date"] or date.today()
            if data["created_at"] is None:
                data.pop("created_at")
            if data["billing_type"] == "one_time":
                data["next_renewal_date"] = None; data["auto_renew"] = False
        elif kind == "currencies":
            rate_base = data.pop("rate_base", settings.exchange_api_base.upper())
            if rate_base != settings.exchange_api_base.upper():
                raise ValueError("Exchange base mismatch")
            rate = data.pop("rate_to_base", None)
            values = CurrencyIn.model_validate(data).model_dump(); values.pop("rate_to_base")
            values["code"] = values["code"].upper()
            if not re.fullmatch(r"[A-Z0-9]{2,8}", values["code"]) or not values["name"].strip():
                raise ValueError("Invalid currency")
            existing = db.get(Currency, values["code"])
            if existing and (not existing.is_custom or existing.user_id != user.id or (not row or existing.code != row.code)):
                raise ValueError("Currency code already exists")
            if row and values["code"] != row.code:
                raise ValueError("Currency code is immutable")
            data = values
            if rate is not None:
                if not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate <= 0:
                    raise ValueError("Invalid exchange rate")
                exchange = db.scalar(select(ExchangeRate).where(ExchangeRate.base == rate_base, ExchangeRate.quote == data["code"]))
                if exchange:
                    exchange.rate = rate; exchange.updated_at = datetime.utcnow()
                else:
                    db.add(ExchangeRate(base=rate_base, quote=data["code"], rate=rate))
        else:
            schema = {"categories": CategoryIn, "payment-methods": PaymentMethodIn, "bundles": BundleIn}[kind]
            if set(data) - set(schema.model_fields) - {"created_at"}:
                raise ValueError("Unknown fields")
            data.pop("created_at", None)
            data = schema.model_validate(data).model_dump()
            if not data["name"].strip():
                raise ValueError("Empty name")
        for column in inspect(model).columns:
            value = data.get(column.key)
            if isinstance(value, str) and getattr(column.type, "length", None) and len(value) > column.type.length:
                raise ValueError("Field too long")
        if row is None:
            row = model(**data, user_id=user.id)
            if kind in ("categories", "payment-methods"):
                row.is_system = False
            if kind == "currencies":
                row.is_custom = True
            db.add(row); db.flush()
            if record is None:
                record = SyncRecord(id=identity, user_id=user.id, kind=kind, entity_pk=_pk(row), version=0, seq=0, deleted=False, readonly=False, fingerprint="", payload=encode({}))
                db.add(record)
            else:
                record.entity_pk = _pk(row); record.deleted = False
        else:
            for key, value in data.items():
                setattr(row, key, value)
    capture(db, user.id)
    return {"op_id": operation.op_id, "status": "applied", "record": envelope(record) if record else None}


def reset_generation(db, user_id):
    lock_account(db, user_id)
    for model in (SyncChange, SyncReceipt, SyncRecord):
        db.execute(delete(model).where(model.user_id == user_id))
    state = _state(db, user_id)
    state.epoch = str(uuid4()); state.cursor = 0
    db.flush()
