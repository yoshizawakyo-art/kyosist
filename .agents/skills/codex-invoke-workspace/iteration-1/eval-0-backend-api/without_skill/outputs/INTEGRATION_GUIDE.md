# FastAPI Login Endpoint Integration Guide

## Overview

This implementation provides a complete authentication system with:
- Email/password login validation
- JWT token generation
- Bcrypt password hashing
- Comprehensive error handling
- Type-safe Pydantic models

## Files Included

1. **auth_service.py** - Core authentication service with:
   - `hash_password()` - Bcrypt password hashing
   - `verify_password()` - Bcrypt password verification
   - `find_user_by_email()` - Database user lookup
   - `generate_jwt_token()` - JWT token generation

2. **login_endpoint.py** - FastAPI endpoint with:
   - `LoginRequest` - Request model (email + password)
   - `LoginResponse` - Response model (token + user info)
   - `register_login_endpoint()` - FastAPI registration function
   - Comprehensive error handling and validation

3. **INTEGRATION_GUIDE.md** - This file

## Step 1: Install Dependencies

Add to your `requirements.txt`:

```
bcrypt==4.1.3
pyjwt==2.8.1
email-validator==2.1.0
```

Then install:

```bash
pip install bcrypt pyjwt email-validator
```

## Step 2: Set Environment Variables

Configure these environment variables before running:

```bash
# In .env file or system environment:
JWT_SECRET_KEY=your-super-secret-key-here-min-32-chars
```

**Important**: In production, use a strong random key. Generate one with:

```python
import secrets
print(secrets.token_urlsafe(32))
```

## Step 3: Add to FastAPI Application

In your `src/api/index.py`:

```python
# Add imports at the top
from api.auth_service import find_user_by_email, verify_password, generate_jwt_token
from api.login_endpoint import register_login_endpoint

# After creating the FastAPI app:
app = FastAPI()

# ... existing middleware and setup code ...

# Register the login endpoint
register_login_endpoint(app, get_supabase_client)

# ... rest of your endpoints ...
```

Alternatively, inline the endpoint directly:

```python
from pydantic import BaseModel, EmailStr
from api.auth_service import find_user_by_email, verify_password, generate_jwt_token

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    user_id: str
    email: str
    expires_in: int

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    try:
        client = get_supabase_client()
        user = find_user_by_email(client, request.email)
        
        if not user or not verify_password(request.password, user['password_hash']):
            raise HTTPException(status_code=401, detail='Invalid email or password')
        
        token = generate_jwt_token(user['id'], user['email'], expires_in_hours=24)
        
        return LoginResponse(
            token=token,
            user_id=user['id'],
            email=user['email'],
            expires_in=24 * 60 * 60
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail='Authentication error') from exc
```

## Step 4: Create Test Users (Optional)

If you need to create test users for development:

```python
from auth_service import hash_password
from supabase import create_client

# Create Supabase client
client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Create a test user
test_user = {
    'email': 'test@example.com',
    'password_hash': hash_password('test123456')
}

result = client.table('users').insert(test_user).execute()
print(result.data)
```

Or via SQL:

```sql
-- Generate a test user with password 'test123456'
INSERT INTO users (email, password_hash) 
VALUES (
    'test@example.com',
    '$2b$12$...' -- bcrypt hash
);
```

## API Usage

### Request

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456"
  }'
```

### Success Response (200 OK)

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "test@example.com",
  "expires_in": 86400
}
```

### Error Response (401 Unauthorized)

```json
{
  "detail": "Invalid email or password"
}
```

## Token Verification (Optional)

To verify tokens on protected endpoints:

```python
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    secret_key = os.environ.get('JWT_SECRET_KEY')
    
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

@app.get("/api/protected")
async def protected_endpoint(user_id: str = Depends(get_current_user)):
    return {"message": f"Hello user {user_id}"}
```

## Security Considerations

1. **Password Storage**: Passwords are hashed with bcrypt (12 rounds) before storage
2. **JWT Secret**: Use a strong, random secret key (minimum 32 characters)
3. **Token Expiration**: Tokens expire after 24 hours (configurable)
4. **HTTPS**: Always use HTTPS in production
5. **Error Messages**: Error messages are generic to prevent user enumeration
6. **Rate Limiting**: Consider adding rate limiting to prevent brute force attacks

## Database Requirements

Ensure the `users` table exists with this schema:

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

## Testing

```python
import pytest
from fastapi.testclient import TestClient
from auth_service import hash_password

client = TestClient(app)

def test_login_success():
    # Assume test user exists: test@example.com / password123
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    data = response.json()
    assert 'token' in data
    assert data['email'] == 'test@example.com'

def test_login_invalid_password():
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert 'Invalid' in response.json()['detail']

def test_login_user_not_found():
    response = client.post('/api/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'password123'
    })
    assert response.status_code == 401
```

## Next Steps

1. Install dependencies
2. Set `JWT_SECRET_KEY` environment variable
3. Add the endpoint to your FastAPI app
4. Test with curl or Postman
5. Implement token verification for protected endpoints
6. Add rate limiting for production
