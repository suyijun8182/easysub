import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone

import pyotp
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import activity
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import RefreshIn, RegisterIn, TokenOut, UserOut
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    token_version,
)
from app.services import email as email_svc

router = APIRouter(prefix="/api/auth", tags=["auth"])


class VerifyEmailIn(BaseModel):
    email: EmailStr
    code: str


def _gen_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


# 登录失败限流（内存版）：同一用户名在锁定窗口内失败过多则暂时拒绝
_FAILS: dict[str, list[float]] = {}
_MAX_FAILS = 8
_LOCK_SECONDS = 900


def _check_lock(username: str) -> None:
    now = time.time()
    fails = [t for t in _FAILS.get(username, []) if now - t < _LOCK_SECONDS]
    _FAILS[username] = fails
    if len(fails) >= _MAX_FAILS:
        raise HTTPException(429, "登录尝试过多，请约 15 分钟后再试")


def _record_fail(username: str) -> None:
    _FAILS.setdefault(username, []).append(time.time())


def _clear_fail(username: str) -> None:
    _FAILS.pop(username, None)


@router.post("/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(400, "用户名已存在")
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(400, "邮箱已被使用")

    is_first = db.scalar(select(User).limit(1)) is None
    need_email = email_svc.smtp_configured() and not is_first
    need_approval = settings.require_admin_approval and not is_first

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_admin=is_first,
        is_active=True,
        email_verified=not need_email,
        is_approved=not need_approval,
    )
    if need_email:
        user.email_code = _gen_code()
        user.email_code_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        user.email_code_sent_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    activity.log("auth.register", f"新用户注册：{user.username}", user=user)

    if need_email:
        try:
            email_svc.send_code(user.email, user.email_code)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(502, f"验证码邮件发送失败：{e}")
        return {"status": "verify", "message": "验证码已发送到邮箱，请查收并验证"}
    if need_approval:
        return {"status": "pending", "message": "注册成功，等待管理员审核通过后即可登录"}
    return {"status": "ok", "message": "注册成功，请登录"}


@router.post("/resend-verification")
def resend_verification(payload: VerifyEmailIn, request: Request, db: Session = Depends(get_db)):
    source = "resend:" + (request.client.host if request.client else "unknown") + ":" + payload.email.lower()
    _check_lock(source)
    user = db.scalar(select(User).where(User.email == payload.email).with_for_update())
    now = datetime.now(timezone.utc)
    if user and not user.email_verified and email_svc.smtp_configured():
        last = user.email_code_sent_at
        if not last or (now - last.replace(tzinfo=timezone.utc)).total_seconds() >= 60:
            user.email_code = _gen_code()
            user.email_code_expires = now + timedelta(minutes=10)
            user.email_code_sent_at = now
            user.email_code_attempts = 0
            db.commit()
            try:
                email_svc.send_code(user.email, user.email_code)
            except Exception:
                pass
    _record_fail(source)
    return {"ok": True}


@router.post("/verify-email")
def verify_email(payload: VerifyEmailIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email).with_for_update())
    if not user or not user.email_code:
        raise HTTPException(400, "无效的验证请求")
    if user.email_code_attempts >= 5:
        raise HTTPException(429, "验证码尝试过多")
    expires = user.email_code_expires
    if expires and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires and datetime.now(timezone.utc) > expires:
        raise HTTPException(400, "验证码已过期，请重新注册")
    if payload.code.strip() != user.email_code:
        user.email_code_attempts += 1
        db.commit()
        raise HTTPException(400, "验证码不正确")

    user.email_verified = True
    user.email_code = None
    user.email_code_expires = None
    db.commit()
    activity.log("auth.verify_email", f"{user.username} 完成邮箱验证", user=user)

    if not user.is_approved and settings.require_admin_approval:
        return {"status": "pending", "message": "邮箱已验证，等待管理员审核通过后即可登录"}
    return {"status": "ok", "message": "邮箱已验证，请登录"}


@router.post("/login", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    otp: str | None = Form(default=None),
    sync_client: bool = Form(default=False),
    db: Session = Depends(get_db),
):
    _check_lock(form.username)
    user = db.scalar(select(User).where(User.username == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        _record_fail(form.username)
        if sync_client and not user:
            raise HTTPException(401, {"code": "ACCOUNT_NOT_REGISTERED", "message": "该账号尚未在此服务器注册", "registration": True})
        raise HTTPException(401, "用户名或密码错误")
    if not user.email_verified:
        raise HTTPException(403, {"code": "EMAIL_VERIFICATION_REQUIRED", "message": "请先完成邮箱验证", "email": user.email})
    if not user.is_approved and settings.require_admin_approval:
        # 审核已关闭（debug19 起默认关闭）时，此前卡在「待审核」的账号也直接放行
        raise HTTPException(403, "账号正在等待管理员审核，请耐心等待")
    if not user.is_active:
        raise HTTPException(403, "账户已被禁用，请联系管理员")
    # 两步验证
    if user.totp_enabled and user.totp_secret:
        if not otp:
            if sync_client:
                raise HTTPException(401, {"code": "OTP_REQUIRED", "message": "请输入网页账号的两步验证码"})
            raise HTTPException(401, "需要两步验证码", headers={"X-2FA-Required": "1"})
        if not pyotp.TOTP(user.totp_secret).verify(otp.strip(), valid_window=1):
            _record_fail(form.username)
            raise HTTPException(401, "两步验证码不正确")
    _clear_fail(form.username)
    activity.log("auth.login", f"用户 {user.username} 登录", user=user)
    return TokenOut(
        access_token=create_access_token(user.id, user.auth_version),
        refresh_token=create_refresh_token(user.id, user.auth_version),
    )


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    email: EmailStr
    code: str
    new_password: str


@router.post("/forgot")
def forgot_password(payload: ForgotIn, request: Request, db: Session = Depends(get_db)):
    """发起找回密码：向邮箱发送重置码。为防用户枚举，无论是否存在都返回成功。"""
    source = "reset-source:" + (request.client.host if request.client else "unknown") + ":" + payload.email.lower()
    _check_lock(source)
    user = db.scalar(select(User).where(User.email == payload.email).with_for_update())
    now = datetime.now(timezone.utc)
    if user and email_svc.smtp_configured():
        last = user.reset_code_sent_at
        if last and (now - last.replace(tzinfo=timezone.utc)).total_seconds() < 60:
            return {"ok": True, "message": "若该邮箱已注册，重置码已发送，请查收邮件"}
        code = _gen_code()
        user.reset_code = hashlib.sha256(code.encode()).hexdigest()
        user.reset_code_expires = now + timedelta(minutes=15)
        user.reset_code_sent_at = now
        user.reset_code_attempts = 0
        db.commit()
        try:
            email_svc.send_reset(user.email, code)
        except Exception:
            pass
    _record_fail(source)
    return {"ok": True, "message": "若该邮箱已注册，重置码已发送，请查收邮件"}


@router.post("/reset")
def reset_password(payload: ResetIn, request: Request, db: Session = Depends(get_db)):
    source = "reset-attempt:" + (request.client.host if request.client else "unknown") + ":" + payload.email.lower()
    _check_lock(source)
    user = db.scalar(select(User).where(User.email == payload.email).with_for_update())
    if not user or not user.reset_code:
        _record_fail(source)
        raise HTTPException(400, "无效的重置请求")
    if user.reset_code_attempts >= 5:
        raise HTTPException(429, "验证码尝试过多，请重新申请验证码")
    expires = user.reset_code_expires
    if not expires or datetime.now(timezone.utc) > expires.replace(tzinfo=timezone.utc):
        raise HTTPException(400, "重置码已过期，请重新发起")
    if not secrets.compare_digest(hashlib.sha256(payload.code.strip().encode()).hexdigest(), user.reset_code):
        user.reset_code_attempts += 1
        db.commit()
        _record_fail(source)
        raise HTTPException(400, "重置码不正确")
    if len(payload.new_password) < 6:
        raise HTTPException(400, "新密码至少 6 位")
    user.password_hash = hash_password(payload.new_password)
    user.auth_version += 1
    user.reset_code = None
    user.reset_code_expires = None
    db.commit()
    _clear_fail(user.username)
    activity.log("auth.reset_password", f"{user.username} 通过邮箱重置了密码", user=user, level="warn")
    return {"ok": True, "message": "密码已重置，请用新密码登录"}


@router.post("/refresh", response_model=TokenOut)
def refresh(payload: "RefreshIn", db: Session = Depends(get_db)):
    user_id = decode_token(payload.refresh_token, "refresh")
    user = db.get(User, user_id) if user_id is not None else None
    if user is None or token_version(payload.refresh_token) != user.auth_version:
        raise HTTPException(401, "刷新令牌无效")
    if not user.is_active or not user.email_verified or (settings.require_admin_approval and not user.is_approved):
        raise HTTPException(403, "账号已禁用或尚未完成验证")
    return TokenOut(
        access_token=create_access_token(user_id, user.auth_version),
        refresh_token=create_refresh_token(user_id, user.auth_version),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


from app.schemas import RefreshIn  # noqa: E402  (避免前向引用问题)
