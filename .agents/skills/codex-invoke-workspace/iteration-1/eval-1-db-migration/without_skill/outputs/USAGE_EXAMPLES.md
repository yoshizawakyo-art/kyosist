# Sessions Table - Usage Examples

## Backend Integration (Python/FastAPI)

```python
from datetime import datetime, timedelta
from uuid import uuid4
import uuid

# Create a new session
def create_session(user_id: str, token: str) -> dict:
    """Create a new session for a user."""
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    from supabase import create_client
    supabase = create_client(url, key)
    
    result = supabase.table('sessions').insert({
        'id': str(uuid4()),
        'user_id': user_id,
        'token': token,
        'expires_at': expires_at.isoformat(),
        'created_at': datetime.utcnow().isoformat()
    }).execute()
    
    return result.data[0] if result.data else None


# Validate a session token
def validate_session(token: str) -> dict | None:
    """Validate if token exists and is not expired."""
    from supabase import create_client
    supabase = create_client(url, key)
    
    result = supabase.table('sessions').select('*').eq('token', token).gte('expires_at', 'NOW()').execute()
    
    return result.data[0] if result.data else None


# Get all active sessions for a user
def get_user_sessions(user_id: str) -> list:
    """Get all non-expired sessions for a user."""
    from supabase import create_client
    supabase = create_client(url, key)
    
    result = supabase.table('sessions').select('*').eq('user_id', user_id).gte('expires_at', 'NOW()').execute()
    
    return result.data


# Revoke a session (logout)
def revoke_session(token: str) -> bool:
    """Delete a session (logout)."""
    from supabase import create_client
    supabase = create_client(url, key)
    
    result = supabase.table('sessions').delete().eq('token', token).execute()
    
    return len(result.data) > 0


# Cleanup expired sessions (run periodically)
def cleanup_expired_sessions() -> int:
    """Delete all expired sessions. Run via cron job."""
    from supabase import create_client
    supabase = create_client(url, key)
    
    result = supabase.table('sessions').delete().lt('expires_at', 'NOW()').execute()
    
    return len(result.data)
```

## Frontend Integration (JavaScript/Fetch)

```javascript
// Store session token in localStorage
function setSessionToken(token) {
  localStorage.setItem('sessionToken', token);
}

// Retrieve session token
function getSessionToken() {
  return localStorage.getItem('sessionToken');
}

// Clear session on logout
function clearSessionToken() {
  localStorage.removeItem('sessionToken');
}

// Validate session on page load
async function validateSession() {
  const token = getSessionToken();
  if (!token) return false;
  
  try {
    const response = await fetch('/api/auth/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.status === 200;
  } catch (error) {
    console.error('Session validation failed:', error);
    return false;
  }
}

// Logout: revoke session server-side
async function logout() {
  const token = getSessionToken();
  if (!token) return;
  
  try {
    await fetch('/api/auth/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
  } finally {
    clearSessionToken();
    window.location.href = '/';
  }
}
```

## FastAPI Middleware Example

```python
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import jwt

app = FastAPI()

# Session validation middleware
@app.middleware("http")
async def validate_session_middleware(request: Request, call_next):
    """Validate session token for protected routes."""
    
    # Skip validation for public routes
    public_routes = ['/api/auth/login', '/api/auth/register', '/']
    if request.url.path in public_routes:
        return await call_next(request)
    
    # Extract token from Authorization header
    auth_header = request.headers.get('authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing or invalid authorization header'
        )
    
    token = auth_header.split(' ')[1]
    
    # Validate session token in database
    from supabase import create_client
    supabase = create_client(url, key)
    
    result = supabase.table('sessions').select('user_id').eq('token', token).gte('expires_at', 'NOW()').execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired session'
        )
    
    # Attach user_id to request state
    request.state.user_id = result.data[0]['user_id']
    
    return await call_next(request)
```

## Direct SQL Examples

```sql
-- List all active sessions with user emails
SELECT 
  s.id,
  s.user_id,
  u.email,
  s.token,
  s.expires_at,
  s.created_at,
  (s.expires_at - NOW()) AS time_remaining
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.expires_at > NOW()
ORDER BY s.created_at DESC;

-- Count sessions per user
SELECT 
  u.email,
  COUNT(s.id) as active_sessions,
  COUNT(CASE WHEN s.expires_at < NOW() THEN 1 END) as expired_sessions
FROM users u
LEFT JOIN sessions s ON u.id = s.user_id
GROUP BY u.id, u.email;

-- Find sessions expiring in next hour
SELECT 
  s.id,
  u.email,
  s.expires_at,
  (s.expires_at - NOW()) AS expires_in
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.expires_at > NOW()
  AND s.expires_at <= NOW() + INTERVAL '1 hour'
ORDER BY s.expires_at ASC;

-- Analyze session creation patterns
SELECT 
  DATE(s.created_at) as date,
  EXTRACT(HOUR FROM s.created_at) as hour,
  COUNT(*) as sessions_created
FROM sessions s
GROUP BY DATE(s.created_at), EXTRACT(HOUR FROM s.created_at)
ORDER BY date DESC, hour DESC;
```

## Environment Setup

### Recommended Configuration

```env
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SESSION_TOKEN_EXPIRY_HOURS=24
SESSION_CLEANUP_INTERVAL_MINUTES=60
```

### Scheduled Cleanup (Using APScheduler)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

def schedule_session_cleanup():
    """Setup background job to cleanup expired sessions every hour."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_expired_sessions, 'interval', hours=1)
    scheduler.start()
    print(f"[{datetime.now()}] Session cleanup scheduler started")

# In FastAPI startup
@app.on_event("startup")
async def startup_event():
    schedule_session_cleanup()
```

## Security Considerations

1. **Token Format**: Use JWTs or cryptographically secure random strings
2. **Token Storage**: Never expose tokens in URLs; use secure cookies or Authorization headers
3. **HTTPS Only**: Always use HTTPS in production
4. **Token Rotation**: Consider rotating tokens periodically
5. **Logout**: Always DELETE the session record on logout
6. **Expiration**: Enforce short expiration times (24 hours recommended)
7. **Rate Limiting**: Apply rate limits to auth endpoints to prevent brute force
