from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(sub: str, expires: timedelta, token_type: str, auth_version: int = 0) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": sub, "type": token_type, "av": auth_version, "iat": now, "exp": now + expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, auth_version: int = 0) -> str:
    return _create_token(
        str(user_id), timedelta(minutes=settings.access_token_expire_minutes), "access", auth_version
    )


def create_refresh_token(user_id: int, auth_version: int = 0) -> str:
    return _create_token(
        str(user_id), timedelta(days=settings.refresh_token_expire_days), "refresh", auth_version
    )


def decode_token(token: str, expected_type: str = "access") -> int | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != expected_type:
            return None
        return int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        return None


def token_version(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return int(payload.get("av", 0))
    except (JWTError, ValueError, TypeError):
        return None


def session_tokens(user) -> dict:
    return {"ok": True, "access_token": create_access_token(user.id, user.auth_version),
            "refresh_token": create_refresh_token(user.id, user.auth_version)}
