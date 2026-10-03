"""Token + password helpers. Hashing lives in app.core.passwords (stdlib only, unit-tested)."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError

from app.core.config import settings
from app.core.passwords import (  # re-exported for existing imports
    hash_password as get_password_hash,
    verify_password,
    verify_and_check_rehash,
)

__all__ = ["get_password_hash", "verify_password", "verify_and_check_rehash",
           "create_access_token", "decode_access_token"]


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({"iat": now, "exp": now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
