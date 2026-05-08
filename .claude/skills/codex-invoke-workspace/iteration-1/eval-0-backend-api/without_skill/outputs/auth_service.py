"""
Authentication service module for user login and JWT token generation.

This module provides functions for:
- Password hashing and verification using bcrypt
- User lookup from the database
- JWT token generation
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from supabase import Client


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash

    Returns:
        A bcrypt-hashed password string (includes salt)
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plaintext_password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Args:
        plaintext_password: The password provided by the user
        password_hash: The stored bcrypt hash from the database

    Returns:
        True if the password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plaintext_password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except ValueError:
        return False


def find_user_by_email(client: Client, email: str) -> dict | None:
    """
    Retrieve a user from the database by email address.

    Args:
        client: Supabase client instance
        email: The user's email address

    Returns:
        User record dict if found, None otherwise
    """
    result = client.table('users').select('*').eq('email', email).execute()
    if result.data:
        return result.data[0]
    return None


def generate_jwt_token(user_id: str, email: str, expires_in_hours: int = 24) -> str:
    """
    Generate a JWT token for authenticated user.

    Args:
        user_id: The user's UUID
        email: The user's email address
        expires_in_hours: Token expiration time in hours (default: 24)

    Returns:
        JWT token string

    Raises:
        ValueError: If JWT_SECRET_KEY environment variable is not set
    """
    secret_key = os.environ.get('JWT_SECRET_KEY')
    if not secret_key:
        raise ValueError('JWT_SECRET_KEY environment variable is not configured')

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=expires_in_hours)

    payload = {
        'sub': user_id,
        'email': email,
        'iat': now,
        'exp': expires_at,
    }

    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token
