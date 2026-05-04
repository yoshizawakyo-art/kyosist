import os
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from .schemas.auth import TokenResponse


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440


def _get_jwt_secret_key() -> str:
    secret_key = os.environ.get("JWT_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured")
    return secret_key


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _get_jwt_secret_key(), algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, _get_jwt_secret_key(), algorithms=[ALGORITHM])


def authenticate_user(
    email: str, password: str, hashed_password: str
) -> TokenResponse | None:
    if not verify_password(password, hashed_password):
        return None

    access_token = create_access_token({"sub": email})
    return TokenResponse(access_token=access_token)
