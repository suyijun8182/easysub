from typing import Literal
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import SyncChange, SyncReceipt, SyncRecord, User
from app.services import sync as service

router = APIRouter(prefix="/api/sync/v1", tags=["sync"])


@router.get("/icons/{identity}")
def download_icon(identity: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.get(SyncRecord, str(identity))
    if not record or record.user_id != user.id or record.deleted:
        raise HTTPException(404, "图标不存在")
    source = service.decode(record.payload).get("icon") or ""
    prefix = "/static/icons/" if source.startswith("/static/icons/") else "/api/icons/library/"
    if not source.startswith(prefix):
        raise HTTPException(404, "此记录没有服务器图标")
    relative = source[len(prefix):]
    root = Path("data/icons" if prefix == "/static/icons/" else "data/icons/library").resolve()
    if prefix != "/static/icons/" and not relative.endswith(".png"):
        relative += ".png"
    path = (root / relative).resolve()
    if root not in path.parents or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
        raise HTTPException(404, "图标不存在或过大")
    return FileResponse(path, headers={"Cache-Control": "private, no-store"})


class Operation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    id: UUID
    kind: Literal["subscriptions", "categories", "payment-methods", "bundles", "currencies", "preferences", "notification-config"]
    base_version: int = Field(ge=0)
    deleted: bool = False
    restore: bool = False
    data: dict = Field(default_factory=dict)

    @field_validator("data")
    @classmethod
    def limit_data(cls, value):
        if len(service.canonical(value).encode()) > 128 * 1024:
            raise ValueError("Operation payload too large")
        return value


class PushIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    epoch: UUID
    device_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    operations: list[Operation] = Field(max_length=100)


def ensure(db, user):
    service.lock_account(db, user.id)
    return service.capture(db, user.id)


@router.get("/capabilities")
def capabilities(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = ensure(db, user)
    result = {"protocol": 1, "account_id": user.id, "username": user.username, "epoch": state.epoch,
              "cursor": state.cursor, "max_batch": 100, "exchange_base": settings.exchange_api_base.upper(),
              "currency_codes": "globally-unique", "conflicts": "preserve-both"}
    result["counts"] = dict(db.execute(select(SyncRecord.kind, func.count()).where(SyncRecord.user_id == user.id, SyncRecord.deleted.is_(False), SyncRecord.readonly.is_(False)).group_by(SyncRecord.kind)).all())
    db.commit()
    return result


@router.get("/changes")
def changes(cursor: int = Query(default=0, ge=0), limit: int = Query(default=200, ge=1, le=500), epoch: str | None = None,
            user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = ensure(db, user)
    if (epoch and epoch != state.epoch) or cursor > state.cursor:
        raise HTTPException(409, {"code": "RESET_REQUIRED", "message": "资料库已恢复或更换，请重新确认合并"})
    rows = db.scalars(select(SyncChange).where(SyncChange.user_id == user.id, SyncChange.seq > cursor, SyncChange.seq <= state.cursor).order_by(SyncChange.seq).limit(limit + 1)).all()
    more = len(rows) > limit
    page = rows[:limit]
    result = {"epoch": state.epoch, "changes": [service.envelope(row) for row in page],
              "next_cursor": page[-1].seq if page else cursor, "has_more": more}
    db.commit()
    return result


@router.post("/push")
def push(payload: PushIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = ensure(db, user)
    if str(payload.epoch) != state.epoch:
        raise HTTPException(409, {"code": "RESET_REQUIRED", "message": "资料库已更换，未写入旧设备数据"})
    results = []
    for operation in payload.operations:
        digest = service.fingerprint(operation.model_dump(mode="json"))
        receipt = db.get(SyncReceipt, (user.id, payload.device_id, operation.op_id))
        if receipt:
            results.append(service.decode(receipt.payload) if receipt.fingerprint == digest else {"op_id": operation.op_id, "status": "rejected", "code": "OP_ID_REUSED"})
            continue
        try:
            with db.begin_nested():
                result = service.apply_operation(db, user, operation)
        except (ValueError, TypeError, KeyError, IntegrityError, DataError):
            result = {"op_id": operation.op_id, "status": "rejected", "code": "INVALID_DATA", "message": "数据格式、字段或关联无效，未应用该操作"}
        db.add(SyncReceipt(user_id=user.id, device_id=payload.device_id, operation_id=operation.op_id, fingerprint=digest, payload=service.encode(result)))
        db.flush()
        results.append(result)
    db.commit()
    return {"epoch": state.epoch, "results": results, "cursor": state.cursor}
