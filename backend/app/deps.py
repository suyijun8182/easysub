from datetime import datetime

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiToken, User
from app.security import decode_token
from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    user_id = decode_token(token, "access")
    if user_id is None:
        # 回退：把 Bearer 当作 API Token 校验（供脚本/自动化访问）
        row = db.scalar(select(ApiToken).where(ApiToken.token == token))
        if row:
            row.last_used_at = datetime.utcnow()
            db.commit()
            user_id = row.user_id
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        from app.services.sync import lock_account
        user = lock_account(db, user_id)
    else:
        user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")
    if not user.email_verified or (settings.require_admin_approval and not user.is_approved):
        raise HTTPException(status_code=403, detail="账号尚未完成验证或审批")
    return user


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user
