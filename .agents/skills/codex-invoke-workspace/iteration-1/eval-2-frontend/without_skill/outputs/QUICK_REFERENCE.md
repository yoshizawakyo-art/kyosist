# Login Form - Quick Reference

## Files
- `login.html` - Page structure (70 lines)
- `login.css` - Styling (240 lines)
- `login.js` - Logic (280 lines)

## Deployment
```bash
mkdir -p src/public/auth
cp login.html src/public/auth/
cp login.css src/public/auth/
cp login.js src/public/auth/
```

## Backend Endpoint
```python
@app.post("/api/auth/login")
async def login(req: LoginRequest) -> LoginResponse:
    # Validate credentials
    # Generate JWT
    return LoginResponse(token=token)
```

## Key Functions

### JavaScript Functions
| Function | Purpose |
|----------|---------|
| `validateEmail()` | Check email format |
| `validatePassword()` | Check password length |
| `validateForm()` | Full form validation |
| `callLoginAPI()` | POST to /api/auth/login |
| `storeAuthToken()` | Save JWT to localStorage |
| `getAuthToken()` | Retrieve JWT from localStorage |
| `handleLoginSubmit()` | Form submission handler |

### Environment Variables
```bash
JWT_SECRET=your-secret-key
JWT_EXPIRATION_HOURS=24
```

## API Endpoints

### Login
```
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
Response: {"token": "jwt..."}
```

### Protected Routes
```
GET /api/conversations
Headers: {"Authorization": "Bearer jwt..."}
```

## Form Validation Rules

| Field | Rules | Error Message |
|-------|-------|---------------|
| Email | Required, Valid format | "有効なメールアドレスを入力してください" |
| Password | Required, Min 6 chars | "パスワードは6文字以上である必要があります" |

## Storage Keys
- Token: `kyosist_auth_token`
- Use: `localStorage.getItem("kyosist_auth_token")`

## Color Scheme
```css
--accent: #7c6ef0;           /* Button, links */
--accent-hover: #6657d8;     /* Button hover */
--main-bg: #f8f7f4;          /* Page background */
--input-bg: #ffffff;         /* Form background */
--text-primary: #1a1826;     /* Text */
--text-muted: #8888a0;       /* Muted text */
--border: #e6e2da;           /* Borders */
```

## Error Handling
```javascript
// Validation error
if (!validateEmail(email)) {
  // Show error message
}

// API error
try {
  const response = await callLoginAPI(email, password);
  storeAuthToken(response.token);
} catch (error) {
  displayFormError(error.message);
}
```

## Token Usage
```javascript
// Get token
const token = getAuthToken();

// Send with request
fetch("/api/endpoint", {
  headers: {
    "Authorization": `Bearer ${token}`
  }
})

// Clear on logout
localStorage.removeItem("kyosist_auth_token");
```

## Testing Checklist
- [ ] Valid credentials → Redirect home
- [ ] Invalid email → Show error
- [ ] Missing fields → Show error
- [ ] Wrong password → Show error
- [ ] Network error → Handle gracefully
- [ ] Mobile responsive → Works on small screens
- [ ] Token stored → localStorage has token
- [ ] Button loading → Shows loading state
- [ ] Logout clears → Token removed

## Common Issues

| Issue | Solution |
|-------|----------|
| Button doesn't work | Check /api/auth/login exists |
| CORS error | Check allow_origins in middleware |
| Token not saving | Check localStorage is enabled |
| No redirect | Verify redirect URL exists |
| Error not showing | Check element IDs match |

## Security Checklist
- [ ] JWT secret in env vars
- [ ] HTTPS in production
- [ ] Rate limiting on endpoint
- [ ] Passwords hashed (bcrypt)
- [ ] Token expiration set
- [ ] CORS configured
- [ ] No password logging
- [ ] Token validated on protected routes

## Performance Tips
1. Minify files for production
2. Enable caching headers
3. Use CDN for static files
4. Implement token refresh
5. Add rate limiting

## Browser Support
- Chrome/Edge: 90+
- Firefox: 88+
- Safari: 14+
- Mobile browsers: Latest versions

## File Sizes
- login.html: 2.0 KB
- login.css: 5.7 KB
- login.js: 7.6 KB
- **Total: 15.3 KB**

## Documentation Files
- `README.md` - Full overview
- `EXECUTION_SUMMARY.md` - Implementation details
- `BACKEND_REQUIREMENTS.md` - API specification
- `INTEGRATION_GUIDE.md` - Step-by-step setup
- `QUICK_REFERENCE.md` - This file

## Important Notes

1. **No External Dependencies**: Pure HTML, CSS, JavaScript
2. **No Lambda Functions**: Follows project coding standards
3. **Responsive Design**: Works on mobile and desktop
4. **i18n Ready**: Japanese text, easily translatable
5. **Accessible**: Proper labels, focus states, error messages
6. **Secure**: JWT in localStorage, password masked
7. **Production Ready**: Comprehensive error handling

## Next: After Login

Implement protected routes that check token:

```javascript
// Redirect if no token
if (!getAuthToken()) {
  window.location.href = "/auth/login.html";
}

// Or use in API calls
const token = getAuthToken();
if (token) {
  fetch("/api/conversations", {
    headers: { "Authorization": `Bearer ${token}` }
  })
}
```

## Customization Examples

### Change API endpoint
```javascript
const LOGIN_API_ENDPOINT = "/api/custom/login";
```

### Change redirect URL
```javascript
window.location.href = "/dashboard/";
```

### Change token key
```javascript
const JWT_TOKEN_KEY = "my_custom_token";
```

### Change colors
```css
:root {
  --accent: #your-color;
}
```

### Add form field
```html
<div class="form-group">
  <label for="remember">Remember me</label>
  <input type="checkbox" id="remember" />
</div>
```

---

**For detailed information, see the documentation files in this directory.**
