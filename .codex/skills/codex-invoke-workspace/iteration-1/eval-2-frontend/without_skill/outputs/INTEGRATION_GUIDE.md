# Login Form Integration Guide

## Quick Start

### 1. Deploy Files to Project
Copy the three files to the project structure:

```bash
# From project root
cp login.html src/public/auth/login.html
cp login.css src/public/auth/login.css
cp login.js src/public/auth/login.js
```

### 2. Create Auth Directory (if needed)
```bash
mkdir -p src/public/auth
```

### 3. Add Route to Index
Ensure your main page (`src/public/index.html`) links to the login page or implements navigation:

```html
<a href="/auth/login.html">ログイン</a>
```

Or for routing:
```html
<script>
  if (!getAuthToken()) {
    window.location.href = '/auth/login.html';
  }
</script>
```

### 4. Implement Backend Endpoint
Create the `/api/auth/login` endpoint in your backend (`src/api/index.py`):

```python
from fastapi import HTTPException
from pydantic import BaseModel
import jwt
import bcrypt

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest) -> LoginResponse:
    client = get_supabase_client()
    
    # Look up user by email
    try:
        result = client.table("users").select("*").eq("email", req.email).single().execute()
        user = result.data
    except Exception:
        raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")
    
    if not user:
        raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")
    
    # Verify password
    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")
    
    # Generate JWT token
    token = jwt.encode(
        {
            "sub": user["id"],
            "email": user["email"],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24),
        },
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    
    return LoginResponse(token=token)
```

### 5. Protect Routes with Token

For protected routes, verify the JWT token:

```python
from fastapi import Header, HTTPException

def verify_token(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="認証トークンが必要です")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="無効なトークンです")

@app.get("/api/user/profile")
async def get_user_profile(token_payload: dict = Depends(verify_token)):
    user_id = token_payload["sub"]
    # Fetch user profile...
    return user_data
```

### 6. Update Frontend to Send Token

When making authenticated API calls, include the token:

```javascript
async function fetchWithAuth(url, options = {}) {
  const token = getAuthToken();
  
  if (!token) {
    throw new Error("認証トークンが見つかりません");
  }
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      "Authorization": `Bearer ${token}`,
    },
  });
  
  if (response.status === 401) {
    // Token expired or invalid
    clearAuthToken();
    window.location.href = "/auth/login.html";
  }
  
  return response;
}

// Usage in other modules
const response = await fetchWithAuth("/api/conversations");
const data = await response.json();
```

## File Locations

After integration, the structure should be:

```
kyosist/
├── src/
│   ├── public/
│   │   ├── index.html
│   │   ├── common/
│   │   │   ├── base.css
│   │   │   ├── kyouCommon.js
│   │   │   └── kyouUtils.js
│   │   ├── auth/                 ← NEW FOLDER
│   │   │   ├── login.html        ← NEW FILE
│   │   │   ├── login.css         ← NEW FILE
│   │   │   └── login.js          ← NEW FILE
│   │   ├── chat/
│   │   │   └── ...
│   │   └── skills/
│   │       └── ...
│   └── api/
│       ├── index.py              ← MODIFY (add /api/auth/login)
│       └── agent_service.py
└── ...
```

## Environment Variables

Add to `.env` file:

```bash
# JWT Configuration
JWT_SECRET=your-very-secret-key-here-minimum-32-chars
JWT_EXPIRATION_HOURS=24

# CORS Configuration (if restricting origins)
ALLOWED_ORIGINS=http://localhost:8000,https://yourdomain.com
```

## Testing the Integration

### 1. Start Backend
```bash
python run.py
```

### 2. Access Login Page
Navigate to: `http://localhost:8000/auth/login.html`

### 3. Test Valid Login
- Email: existing_user@example.com
- Password: correct_password
- Expected: Token stored, redirect to home page

### 4. Test Invalid Credentials
- Email: nonexistent@example.com or wrong@example.com
- Password: wrongpassword
- Expected: Error message displayed

### 5. Verify Token Storage
Open browser DevTools → Application → Local Storage → Find `kyosist_auth_token`

### 6. Test Protected Route
Make API call with token:
```javascript
const token = localStorage.getItem("kyosist_auth_token");
fetch("/api/conversations", {
  headers: {
    "Authorization": `Bearer ${token}`
  }
})
.then(r => r.json())
.then(console.log);
```

## Customization

### Change Token Storage Key
In `login.js`, modify:
```javascript
const JWT_TOKEN_KEY = "your_custom_key";
```

### Change API Endpoint
In `login.js`, modify:
```javascript
const LOGIN_API_ENDPOINT = "/api/your-custom-endpoint";
```

### Change Styling
Edit `login.css` to match your brand colors. Key variables:
```css
--accent: #7c6ef0;           /* Primary button color */
--accent-hover: #6657d8;     /* Button hover color */
--main-bg: #f8f7f4;          /* Page background */
--input-bg: #ffffff;         /* Form background */
--text-primary: #1a1826;     /* Text color */
```

### Add Additional Form Fields
In `login.html`, add new form group:
```html
<div class="form-group">
  <label for="remember" class="form-label">ログイン状態を保存</label>
  <input type="checkbox" id="remember" name="remember" />
</div>
```

In `login.js`, update `LoginRequest` handling:
```javascript
const rememberMe = document.getElementById("remember").checked;
```

### Change Password Validation Rules
In `login.js`, modify `validatePassword()`:
```javascript
function validatePassword(passwordInput) {
  const passwordValue = passwordInput.value;
  
  if (passwordValue.length < 8) {  // Change minimum length
    // ...
  }
  
  // Add additional rules (uppercase, special chars, etc.)
}
```

## Troubleshooting

### Issue: "Cannot find module" error
**Solution**: Ensure files are in correct directory:
```bash
ls -la src/public/auth/
# Should show: login.html, login.css, login.js
```

### Issue: Login button doesn't work
**Solution**: Check browser console for errors. Common causes:
- `/api/auth/login` endpoint not implemented
- CORS issue - check `allow_origins` in FastAPI middleware
- Network error - verify backend is running

### Issue: Token not storing in localStorage
**Solution**: Check browser privacy settings:
- Some browsers block localStorage in private mode
- Check localStorage is enabled: `typeof(Storage) !== "undefined"`

### Issue: Page doesn't redirect after login
**Solution**: Check redirect URL in `login.js`:
```javascript
window.location.href = "/";  // Ensure this path exists
```

### Issue: Form validation error messages not showing
**Solution**: Verify HTML element IDs match JavaScript references:
```javascript
document.getElementById("email-error");     // Must exist in HTML
document.getElementById("password-error");  // Must exist in HTML
```

## Security Checklist

- [ ] JWT secret is stored in environment variables
- [ ] JWT secret is never committed to git
- [ ] Backend validates password securely (bcrypt/argon2)
- [ ] CORS is configured appropriately (not `["*"]` in production)
- [ ] HTTPS is used in production
- [ ] Rate limiting is implemented
- [ ] Passwords are never logged
- [ ] Token expiration is implemented
- [ ] Token refresh mechanism is considered
- [ ] Logout functionality clears token from localStorage

## Performance Optimization

### 1. Lazy Load CSS
In `login.html`:
```html
<link rel="stylesheet" href="login.css" media="screen and (min-width: 0)">
```

### 2. Minify Files for Production
Use build tools like esbuild or terser:
```bash
esbuild login.js --minify --outfile=login.min.js
```

### 3. Add Caching Headers
In backend:
```python
@app.get("/auth/login.html")
async def get_login():
    headers = {
        "Cache-Control": "public, max-age=3600"
    }
    return FileResponse("src/public/auth/login.html", headers=headers)
```

## Browser Support

- Chrome/Edge: 90+
- Firefox: 88+
- Safari: 14+
- Mobile browsers: iOS Safari 14+, Chrome Android 90+

## Accessibility Improvements

Consider adding:
- ARIA labels for screen readers
- Live regions for error announcements
- Keyboard navigation support
- High contrast mode support

```html
<input
  type="email"
  id="email"
  aria-label="メールアドレス入力欄"
  aria-describedby="email-error"
/>
<span id="email-error" role="alert" class="form-error"></span>
```

## Next Steps

1. Implement backend `/api/auth/login` endpoint
2. Set up JWT secret in environment variables
3. Create users table in database
4. Implement password hashing
5. Deploy files to project
6. Test login flow end-to-end
7. Implement logout functionality
8. Add token refresh mechanism
9. Protect API routes with authentication
10. Add signup/registration page
