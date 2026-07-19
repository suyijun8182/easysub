import base64
import io
import secrets as _secrets
from datetime import datetime

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import activity
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import ApiToken, User
from app.schemas import UserOut, UserUpdate
from app.security import hash_password, verify_password

router = APIRouter(prefix="/api/me", tags=["me"])


class AccountUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.patch("", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/account", response_model=UserOut)
def update_account(
    payload: AccountUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.username and payload.username != user.username:
        if db.scalar(select(User).where(User.username == payload.username)):
            raise HTTPException(400, "用户名已存在")
        user.username = payload.username
    if payload.email and payload.email != user.email:
        if db.scalar(select(User).where(User.email == payload.email)):
            raise HTTPException(400, "邮箱已被使用")
        user.email = payload.email
    db.commit()
    db.refresh(user)
    activity.log("account.update", f"修改账号信息：{user.username}", user=user)
    return user


@router.post("/password")
def change_password(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(400, "原密码不正确")
    if len(payload.new_password) < 6:
        raise HTTPException(400, "新密码至少 6 位")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    activity.log("account.password", "修改了登录密码", user=user, level="warn")
    return {"ok": True}


# ---------- 两步验证（TOTP）----------
class OtpIn(BaseModel):
    code: str


class PwdIn(BaseModel):
    password: str


@router.post("/2fa/setup")
def twofa_setup(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """生成新的 TOTP 密钥（尚未启用），返回 otpauth 链接与二维码 PNG（data-uri）。"""
    secret = pyotp.random_base32()
    user.totp_secret = secret
    user.totp_enabled = False
    db.commit()
    issuer = "EasySub"
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.username, issuer_name=issuer)
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_data = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    return {"secret": secret, "otpauth_url": uri, "qr": qr_data}


@router.post("/2fa/enable")
def twofa_enable(payload: OtpIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.totp_secret:
        raise HTTPException(400, "请先生成密钥")
    if not pyotp.TOTP(user.totp_secret).verify(payload.code.strip(), valid_window=1):
        raise HTTPException(400, "验证码不正确")
    user.totp_enabled = True
    db.commit()
    activity.log("account.2fa_enable", "开启了两步验证", user=user, level="warn")
    return {"ok": True}


@router.post("/2fa/disable")
def twofa_disable(payload: PwdIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(400, "密码不正确")
    user.totp_enabled = False
    user.totp_secret = None
    db.commit()
    activity.log("account.2fa_disable", "关闭了两步验证", user=user, level="warn")
    return {"ok": True}


# ---------- API Token ----------
class TokenCreateIn(BaseModel):
    name: str


@router.get("/tokens")
def list_tokens(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(ApiToken).where(ApiToken.user_id == user.id).order_by(ApiToken.id.desc())).all()
    return [{
        "id": r.id, "name": r.name,
        "masked": (r.token[:6] + "…" + r.token[-4:]) if r.token else "",
        "created_at": r.created_at, "last_used_at": r.last_used_at,
    } for r in rows]


@router.post("/tokens")
def create_token(payload: TokenCreateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    token = _secrets.token_urlsafe(32)
    row = ApiToken(user_id=user.id, name=payload.name.strip() or "token", token=token)
    db.add(row)
    db.commit()
    db.refresh(row)
    activity.log("account.token_create", f"创建 API Token「{row.name}」", user=user)
    # 完整 token 仅此次返回
    return {"id": row.id, "name": row.name, "token": token}


@router.delete("/tokens/{token_id}")
def delete_token(token_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.get(ApiToken, token_id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "Token 不存在")
    db.delete(row)
    db.commit()
    activity.log("account.token_delete", f"删除 API Token「{row.name}」", user=user, level="warn")
    return {"ok": True}
