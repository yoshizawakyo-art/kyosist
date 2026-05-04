import os
from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from src.api.schemas.auth import TokenResponse


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    secret_key = os.environ["JWT_SECRET_KEY"]
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


def authenticate_user(
    email: str, password: str, hashed_password: str
) -> TokenResponse | None:
    if not verify_password(password, hashed_password):
        return None

    access_token = create_access_token({"sub": email})
    return TokenResponse(access_token=access_token)
