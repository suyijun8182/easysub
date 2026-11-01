from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app import activity
from app.database import get_db
from app.deps import get_admin_user
from app.models import (
    Bundle,
    Category,
    Currency,
    NotificationLog,
    PaymentMethod,
    Subscription,
    User,
)
from app.schemas import AdminUserCreate, AdminUserOut, AdminUserUpdate
from app.security import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _count_admins(db: Session) -> int:
    return db.scalar(
        select(func.count()).select_from(User).where(User.is_admin.is_(True))
    )


def _to_out(db: Session, u: User) -> AdminUserOut:
    out = AdminUserOut.model_validate(u)
    out.subscription_count = db.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.user_id == u.id)
    )
    return out


@router.get("/users", response_model=list[AdminUserOut])
def list_users(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.id)).all()
    return [_to_out(db, u) for u in users]


@router.post("/users", response_model=AdminUserOut)
def create_user(
    payload: AdminUserCreate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(400, "用户名已存在")
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(400, "邮箱已被使用")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_admin=payload.is_admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    activity.log("admin.user_create", f"管理员创建用户「{user.username}」", user=admin)
    return _to_out(db, user)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    from app.services.sync import lock_account
    user = lock_account(db, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")

    # 防止移除/禁用最后一个管理员，导致系统无人可管
    if user.is_admin and (payload.is_admin is False or payload.is_active is False):
        if _count_admins(db) <= 1:
            raise HTTPException(400, "不能停用或降级唯一的管理员")
    if user.id == admin.id and payload.is_active is False:
        raise HTTPException(400, "不能禁用自己的账户")

    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.is_approved is not None:
        user.is_approved = payload.is_approved
        if payload.is_approved:
            activity.log(
                "admin.user_approve", f"管理员审核通过用户「{user.username}」", user=admin
            )
    if payload.password:
        user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return _to_out(db, user)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    from app.services.sync import lock_account
    user = lock_account(db, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    if user.id == admin.id:
        raise HTTPException(400, "不能删除自己的账户")
    if user.is_admin and _count_admins(db) <= 1:
        raise HTTPException(400, "不能删除唯一的管理员")

    # 清理该用户的全部数据（保持外键完整）
    db.execute(delete(NotificationLog).where(NotificationLog.user_id == user_id))
    db.execute(delete(Subscription).where(Subscription.user_id == user_id))
    db.execute(delete(Bundle).where(Bundle.user_id == user_id))
    db.execute(delete(Category).where(Category.user_id == user_id))
    db.execute(delete(PaymentMethod).where(PaymentMethod.user_id == user_id))
    db.execute(delete(Currency).where(Currency.user_id == user_id))
    uname = user.username
    db.delete(user)
    db.commit()
    activity.log("admin.user_delete", f"管理员删除用户「{uname}」及其数据", user=admin, level="warn")
    return {"ok": True}
