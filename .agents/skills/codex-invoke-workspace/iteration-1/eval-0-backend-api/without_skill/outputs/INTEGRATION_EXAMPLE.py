"""
Example showing how to integrate the login endpoint into src/api/index.py

This demonstrates the minimal changes needed to add authentication to the
existing Kyosist FastAPI application.
"""

# ============================================================================
# OPTION 1: Add endpoint directly in src/api/index.py (Simplest)
# ============================================================================

# Add these imports at the top of src/api/index.py
import asyncio
from pydantic import BaseModel, EmailStr

# These are from the provided auth_service.py module
# You would add auth_service.py to src/api/ directory
from api.auth_service import (
    find_user_by_email,
    verify_password,
    generate_jwt_token,
)


# Add these models after existing models
class LoginRequest(BaseModel):
    """Login request with email and password."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Successful login response with JWT token."""
    token: str
    user_id: str
    email: str
    expires_in: int


# Add this helper function after the existing helper functions
def _authenticate_user(client, email: str, password: str) -> dict:
    """
    Authenticate user with email and password.

    Args:
        client: Supabase client
        email: User email
        password: User password

    Returns:
        Dict with token, user_id, email, expires_in

    Raises:
        HTTPException: If credentials invalid (401) or other errors (500)
    """
    user = find_user_by_email(client, email)

    if not user or not verify_password(password, user['password_hash']):
        raise HTTPException(
            status_code=401,
            detail='Invalid email or password'
        )

    token = generate_jwt_token(user['id'], user['email'], expires_in_hours=24)

    return {
        'token': token,
        'user_id': user['id'],
        'email': user['email'],
        'expires_in': 24 * 60 * 60,
    }


# Add this endpoint with other endpoints
@app.post('/api/auth/login', response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate user and return JWT token.

    POST /api/auth/login

    Request:
        {
            "email": "user@example.com",
            "password": "password123"
        }

    Response:
        {
            "token": "eyJhbGci...",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "expires_in": 86400
        }

    Raises:
        HTTPException(401): Invalid email or password
        HTTPException(500): Server error
    """
    try:
        client = get_supabase_client()
        result = await asyncio.to_thread(_authenticate_user, client, request.email, request.password)
        return LoginResponse(**result)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=500, detail='Server configuration error') from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail='Authentication error') from exc


# ============================================================================
# OPTION 2: Use register_login_endpoint function (Cleaner for large apps)
# ============================================================================

from api.login_endpoint import register_login_endpoint

# After creating FastAPI app, add:
app = FastAPI()

# ... existing middleware setup ...

# Register the login endpoint
register_login_endpoint(app, get_supabase_client)

# ... rest of your endpoints ...


# ============================================================================
# OPTION 3: Create separate auth.py module (Best for modularity)
# ============================================================================

# In src/api/auth.py, import and re-export:
from fastapi import FastAPI
from api.login_endpoint import register_login_endpoint

def setup_auth_endpoints(app: FastAPI, get_supabase_client) -> None:
    """Register all authentication endpoints."""
    register_login_endpoint(app, get_supabase_client)

# Then in src/api/index.py:
from api.auth import setup_auth_endpoints

app = FastAPI()

# ... existing setup ...

# Register auth endpoints
setup_auth_endpoints(app, get_supabase_client)

# ... rest of endpoints ...


# ============================================================================
# OPTIONAL: Add token verification for protected endpoints
# ============================================================================

import jwt
import os
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from fastapi import Depends

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """
    Verify JWT token and extract user ID.

    Usage: @app.get("/api/protected")
           async def protected(user_id: str = Depends(get_current_user)):
               return {"user_id": user_id}
    """
    token = credentials.credentials
    secret_key = os.environ.get('JWT_SECRET_KEY')

    if not secret_key:
        raise HTTPException(status_code=500, detail='Server error')

    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        user_id = payload.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail='Invalid token')
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')


# Example protected endpoint:
@app.get('/api/protected')
async def protected_endpoint(user_id: str = Depends(get_current_user)) -> dict:
    """
    Example protected endpoint that requires valid JWT token.

    Usage:
        curl -X GET http://localhost:8000/api/protected \
          -H "Authorization: Bearer <your-jwt-token>"
    """
    return {'message': f'Hello user {user_id}'}


# ============================================================================
# INTEGRATION CHECKLIST
# ============================================================================

# 1. Copy auth_service.py to src/api/
#    cp auth_service.py src/api/

# 2. Update requirements.txt
#    Add:
#    bcrypt==4.1.3
#    pyjwt==2.8.1
#    email-validator==2.1.0

# 3. Set environment variable
#    export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# 4. Choose integration option above and add to src/api/index.py

# 5. Test the endpoint
#    curl -X POST http://localhost:8000/api/auth/login \
#      -H "Content-Type: application/json" \
#      -d '{"email": "test@example.com", "password": "test123"}'

# 6. Run tests
#    pytest test_login.py -v

# ============================================================================
