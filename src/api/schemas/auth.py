import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class AuthUserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LoginResponse(BaseModel):
    token: str
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: AuthUserResponse


class LogoutResponse(BaseModel):
    success: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
