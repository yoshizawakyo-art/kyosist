"""
Login endpoint for FastAPI authentication.

This module defines the /api/auth/login endpoint that:
1. Accepts email and password
2. Validates credentials against the users table
3. Returns a JWT token on success
4. Returns appropriate error responses for invalid credentials

Usage:
    Include this in your FastAPI app:

    from auth_service import find_user_by_email, verify_password, generate_jwt_token

    @app.post("/api/auth/login", response_model=LoginResponse)
    async def login(request: LoginRequest) -> LoginResponse:
        ...
"""

import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import Client

from auth_service import find_user_by_email, verify_password, generate_jwt_token


class LoginRequest(BaseModel):
    """
    Request model for login endpoint.

    Attributes:
        email: User's email address (must be valid email format)
        password: User's plaintext password
    """

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """
    Response model for successful login.

    Attributes:
        token: JWT authentication token
        user_id: UUID of authenticated user
        email: Email address of authenticated user
        expires_in: Token expiration time in seconds
    """

    token: str
    user_id: str
    email: str
    expires_in: int


class LoginErrorResponse(BaseModel):
    """Response model for login errors."""

    detail: str


def _authenticate_user(client: Client, email: str, password: str) -> dict:
    """
    Internal function to authenticate a user.

    Args:
        client: Supabase client instance
        email: User's email address
        password: Plaintext password to verify

    Returns:
        Dict containing token, user_id, email, expires_in

    Raises:
        HTTPException: If credentials are invalid (401) or user not found (401)
    """
    # Look up user by email
    user = find_user_by_email(client, email)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Generate JWT token (24 hour expiration)
    token = generate_jwt_token(user["id"], user["email"], expires_in_hours=24)

    return {
        "token": token,
        "user_id": user["id"],
        "email": user["email"],
        "expires_in": 24 * 60 * 60,  # 24 hours in seconds
    }


def register_login_endpoint(app: FastAPI, get_supabase_client) -> None:
    """
    Register the login endpoint on a FastAPI app.

    Args:
        app: FastAPI application instance
        get_supabase_client: Callable that returns a Supabase Client instance
    """

    @app.post(
        "/api/auth/login",
        response_model=LoginResponse,
        responses={
            401: {"model": LoginErrorResponse, "description": "Invalid credentials"},
        },
    )
    async def login(request: LoginRequest) -> LoginResponse:
        """
        Authenticate user and return JWT token.

        POST /api/auth/login

        Args:
            request: LoginRequest containing email and password

        Returns:
            LoginResponse with JWT token and user info

        Raises:
            HTTPException(401): If email/password combination is invalid
            HTTPException(500): If database or JWT generation fails
        """
        try:
            client = get_supabase_client()
            result = await asyncio.to_thread(
                _authenticate_user, client, request.email, request.password
            )
            return LoginResponse(**result)
        except HTTPException:
            raise
        except ValueError as exc:
            # JWT_SECRET_KEY not configured
            raise HTTPException(
                status_code=500, detail="Server configuration error"
            ) from exc
        except Exception as exc:
            # Database or other unexpected error
            raise HTTPException(
                status_code=500, detail="Authentication service error"
            ) from exc
