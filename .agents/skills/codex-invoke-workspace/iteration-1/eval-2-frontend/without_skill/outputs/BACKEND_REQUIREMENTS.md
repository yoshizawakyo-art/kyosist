# Backend Requirements for Login Form Integration

## API Endpoint Specification

The frontend expects a `/api/auth/login` POST endpoint that accepts user credentials and returns a JWT token.

### Request Format
```
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

### Response Format (Success - 200 OK)
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Response Format (Error - 401/403)
```json
{
  "detail": "メールアドレスまたはパスワードが正しくありません"
}
```

### Response Format (Validation Error - 400)
```json
{
  "detail": "メールアドレスは必須です"
}
```

## Implementation Notes for Backend

### 1. Endpoint Definition (FastAPI)
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI()

class LoginRequest(BaseModel):
    email: str  # EmailStr for validation
    password: str

class LoginResponse(BaseModel):
    token: str

@app.post("/api/auth/login", response_model=LoginResponse, status_code=200)
async def login(req: LoginRequest) -> LoginResponse:
    # Implementation here
    pass
```

### 2. JWT Token Generation
The token should be a valid JWT with the following claims:
```json
{
  "sub": "user_id_uuid",
  "email": "user@example.com",
  "iat": 1234567890,
  "exp": 1234567890
}
```

Recommended libraries:
- `PyJWT` for token encoding/decoding
- `python-jose` for more advanced JWT operations

### 3. Password Validation
- Hash passwords using bcrypt or argon2
- Never store plain-text passwords
- Compare against stored hash: `bcrypt.checkpw(password.encode(), stored_hash)`

### 4. User Lookup
- Query the users table by email
- Handle case sensitivity appropriately (emails are case-insensitive)
- Return appropriate error message if user not found

### 5. Error Messages
Frontend expects error response in this format:
```json
{
  "detail": "Human-readable error message in Japanese or English"
}
```

Common error scenarios:
- User not found: "メールアドレスが登録されていません"
- Wrong password: "パスワードが正しくありません"
- Account disabled: "このアカウントは無効になっています"
- Rate limiting: "ログイン試行回数が多すぎます。しばらく待ってからお試しください"

### 6. CORS Configuration
Ensure CORS is configured to allow POST requests:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 7. Rate Limiting (Recommended)
Implement rate limiting to prevent brute force attacks:
- Limit failed login attempts per email
- Implement exponential backoff or temporary account lockout
- Log suspicious activity

### 8. Token Expiration
Set appropriate token expiration:
- Short-lived access tokens (15-30 minutes)
- Implement refresh token mechanism for long sessions
- Include expiration time (`exp` claim) in JWT

### 9. Session Management (Optional)
Consider implementing:
- Token blacklist on logout
- Session tracking in database
- Multiple device support
- "Remember me" functionality

## Frontend Integration

The login form (`login.js`) will:
1. Call `POST /api/auth/login` with email and password
2. Store the returned JWT in `localStorage` with key `kyosist_auth_token`
3. Send JWT in subsequent requests via Authorization header:
   ```
   Authorization: Bearer <token>
   ```

Backend should validate this header on protected routes.

## Database Requirements

Users table should include:
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);
```

Consider adding:
- Last login timestamp
- Failed login attempt count
- Account lockout fields
- Email verification status

## Security Considerations

1. **HTTPS Only**: Always use HTTPS in production
2. **Secure Headers**: Add security headers
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Strict-Transport-Security: max-age=31536000`

3. **Input Validation**: Validate email and password server-side
4. **Rate Limiting**: Protect against brute force attacks
5. **Logging**: Log login attempts (without passwords)
6. **Token Validation**: Always validate JWT on protected endpoints
7. **CORS**: Restrict origins in production
8. **Database**: Use parameterized queries to prevent SQL injection

## Testing Checklist

- [ ] Valid email + password returns token
- [ ] Invalid email returns 400 with error message
- [ ] Missing fields return 400 with error message
- [ ] Non-existent user returns 401 with error message
- [ ] Wrong password returns 401 with error message
- [ ] Token format is valid JWT
- [ ] Token contains necessary claims (sub, email, exp)
- [ ] Token can be verified on protected routes
- [ ] Response time is acceptable (< 1s)
- [ ] Rate limiting works for multiple failed attempts
- [ ] CORS headers are present in response

## Example Response Flow

```
Frontend Request:
POST /api/auth/login HTTP/1.1
Content-Type: application/json
{
  "email": "user@example.com",
  "password": "mypassword"
}

Backend Processing:
1. Validate email format
2. Look up user by email
3. Compare password hash
4. Generate JWT token
5. Return token in response

Backend Response:
HTTP/1.1 200 OK
Content-Type: application/json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZW1haWwiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYzMjU0MjJ9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
}

Frontend Processing:
1. Parse response
2. Extract token
3. Store in localStorage
4. Redirect to home page
```

## Deployment Considerations

1. Store JWT secret in environment variables (not in code)
2. Keep JWT secret secure and never expose to frontend
3. Rotate JWT secret periodically
4. Monitor login failures for security threats
5. Implement audit logging for compliance
6. Test token expiration and refresh flows
7. Ensure database connections are pooled and efficient

## Future Enhancements

1. Two-factor authentication (2FA)
2. Social login (Google, GitHub)
3. Password reset flow
4. Email verification
5. Account recovery options
6. Login history and device management
7. Passwordless authentication (magic links)
8. Biometric authentication
