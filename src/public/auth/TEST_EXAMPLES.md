# Login Form - Test Examples and Expected Results

## Form Submission Scenarios

### Scenario 1: Valid Login

**Input:**
- Email: `user@example.com`
- Password: `securePassword123`

**Expected Behavior:**
1. Form validation passes
2. Loading spinner appears
3. POST request sent to `/api/auth/login`
4. Server returns token and user data
5. localStorage updated with token and user
6. Success message displays (green)
7. 1 second delay
8. Redirect to `/chat/index.html`

**Console Output:**
```
Network Request: POST /api/auth/login
Request Body: {"email":"user@example.com","password":"securePassword123"}
Response: {"token":"eyJ0eXAi...","user":{"id":"u_202605041200","email":"user@example.com"}}
localStorage: {kyosist_token: "eyJ0eXAi...", kyosist_user: "{...}"}
Redirect: /chat/index.html
```

---

### Scenario 2: Invalid Email Format

**Input:**
- Email: `notanemail`
- Password: `validPassword123`

**Expected Behavior:**
1. On blur of email field: inline error message appears
2. Email input shows red border
3. Submit button is available
4. On submit: error message appears again
5. No API call made
6. User stays on form

**Error Message:**
```
有効なメールアドレスを入力してください
```

---

### Scenario 3: Password Too Short

**Input:**
- Email: `user@example.com`
- Password: `short`

**Expected Behavior:**
1. On blur of password field: inline error message appears
2. Password input shows red border
3. Submit button is available
4. On submit: error message appears again
5. No API call made
6. User stays on form

**Error Message:**
```
パスワードは8文字以上である必要があります
```

---

### Scenario 4: Empty Form Submission

**Input:**
- Email: (empty)
- Password: (empty)

**Expected Behavior:**
1. Submit button clicked
2. Both error messages appear
3. Both inputs show red borders
4. No API call made
5. User stays on form

**Error Messages:**
```
メールアドレスを入力してください
パスワードを入力してください
```

---

### Scenario 5: Invalid Credentials

**Input:**
- Email: `user@example.com`
- Password: `wrongpassword123`

**Expected Behavior:**
1. Form validation passes
2. Loading spinner appears
3. POST request sent to `/api/auth/login`
4. Server returns 401 with error message
5. Loading spinner hides
6. API error message displays (red banner)
7. localStorage is NOT updated
8. User stays on form

**API Response:**
```json
HTTP 401 Unauthorized
{
  "detail": "Invalid credentials"
}
```

**UI Message:**
```
Invalid credentials
```

---

### Scenario 6: Network Error (Server Down)

**Input:**
- Email: `user@example.com`
- Password: `validPassword123`

**Expected Behavior:**
1. Form validation passes
2. Loading spinner appears
3. Network request fails (timeout or no response)
4. Error caught in try-catch block
5. User-friendly error message displays
6. localStorage is NOT updated
7. User stays on form
8. Button is re-enabled

**UI Message:**
```
ネットワークエラーが発生しました。もう一度お試しください。
```

**Console Error:**
```javascript
ログインエラー: TypeError: Failed to fetch
```

---

### Scenario 7: Already Logged In (Session Exists)

**Input:**
- User navigates to `/auth/login.html`
- localStorage already contains `kyosist_token`

**Expected Behavior:**
1. JavaScript init() runs
2. Checks for existing token in localStorage
3. Token found
4. Immediately redirects to `/chat/index.html`
5. User never sees login form

**Console Output:**
```
// Token found, redirecting...
window.location.href = '/chat/index.html'
```

---

### Scenario 8: Real-time Validation - Email

**Input Sequence:**
1. Click email field
2. Type "notanemail"
3. Tab/click away
4. Error message appears

**Expected:**
- Email field gets `aria-invalid="true"`
- Red border appears
- Error text displays immediately
- User can correct without submitting

**Error State:**
```html
<input aria-invalid="true" class="form-input">
<!-- Background becomes light red, border becomes red -->
```

---

### Scenario 9: Real-time Validation - Password

**Input Sequence:**
1. Click password field
2. Type "short"
3. Tab/click away
4. Error message appears

**Expected:**
- Password field gets `aria-invalid="true"`
- Red border appears
- Error text displays immediately
- User can correct without submitting

**Error Message:**
```
パスワードは8文字以上である必要があります
```

---

### Scenario 10: Form Recovery After Error

**Input Sequence:**
1. Submit form with invalid email
2. Error displays
3. Correct the email
4. Tab away from email field
5. Error clears
6. Submit form again

**Expected Behavior:**
1. First submission shows error
2. Email field still shows red state
3. User corrects and tabs away
4. Error message disappears
5. Email field border returns to normal
6. Second submission succeeds

---

## Accessibility Testing

### Keyboard Navigation

**Input:**
- Use only Tab and keyboard to navigate

**Expected Behavior:**
```
1. Tab → Focus moves to Email input
2. Type email
3. Tab → Focus moves to Password input
4. Type password
5. Tab → Focus moves to Submit button
6. Enter → Form submits
```

### Screen Reader Output

**Using NVDA/JAWS:**

```
"Email, edit text, required"
"Password, edit text, required"
"Login, button"
```

**On Error:**

```
"Email, edit text, required, invalid"
"有効なメールアドレスを入力してください"
```

---

## Mobile Testing

### Portrait View (375px width)

**Expected:**
- Login card fits with padding
- Inputs are full width
- Button is full width
- Text is readable
- Touch targets are ≥44px

### Landscape View (667px width)

**Expected:**
- Layout adjusts for width
- Card width capped
- Inputs remain usable
- No horizontal scroll

### Touch Interaction

**Expected:**
- No hover states on touch
- Focus visible on tap
- Keyboard appears on input
- No double-tap zoom needed (viewport set correctly)

---

## Dark Mode Testing

### In Dark Mode (prefers-color-scheme: dark)

**Colors Change:**
- Text: Light gray (#f3f4f6)
- Background: Dark gray (#1f2937)
- Borders: Dark gray (#374151)
- Card: Dark background

**Expected:**
- High contrast maintained
- Error states still visible
- Readable in dark environment
- No harsh white backgrounds

---

## Performance Testing

### Page Load

**Metrics:**
```
Time to First Byte: < 50ms
DOM Content Loaded: < 100ms
Page Interactive: < 300ms
```

### API Call Performance

**Expected Times:**
```
Request Latency: 200-500ms (simulated)
Response Time: < 100ms
Total Time to Redirect: < 1000ms
```

---

## Browser-Specific Testing

### Chrome/Edge

```
✓ All features working
✓ Dark mode support
✓ localStorage works
✓ Fetch API works
✓ Animations smooth
```

### Firefox

```
✓ Form validation works
✓ CSS variables recognized
✓ localStorage works
✓ Animation performance good
```

### Safari

```
✓ CSS gradients render
✓ localStorage supported
✓ Fetch API works
✓ No vendor prefixes needed
```

### Mobile Safari (iOS)

```
✓ Touch interactions work
✓ Keyboard appears correctly
✓ Input focus visible
✓ No zoom issues
✓ Viewport set correctly
```

---

## Edge Cases

### Case 1: Email with Special Characters

**Input:**
- Email: `user+tag@example.co.uk`

**Expected:**
- Passes validation
- API call made
- No issues

---

### Case 2: Very Long Password

**Input:**
- Password: (64+ characters)

**Expected:**
- Validation passes
- No input truncation
- No display issues
- API handles it

---

### Case 3: Rapid Form Submission

**Input:**
- Click submit
- Click submit again immediately

**Expected:**
- Button disabled after first click
- Only one API request
- Loading spinner appears once
- No double submission

---

### Case 4: Slow Network

**Input:**
- Throttle network to 3G
- Submit form

**Expected:**
- Loading spinner visible
- User can see request is pending
- Timeout handled gracefully
- No UI freezing

---

### Case 5: Copy/Paste Credentials

**Input:**
- Copy email from another source
- Paste into form
- Tab to password
- Type password
- Submit

**Expected:**
- Works normally
- Pasted content validated
- No encoding issues
- Form submits

---

## Validation Rule Details

### Email Validation Regex

```javascript
/^[^\s@]+@[^\s@]+\.[^\s@]+$/
```

**Valid Examples:**
```
user@example.com
john.doe@company.co.uk
test+tag@domain.org
```

**Invalid Examples:**
```
notanemail
@example.com
user@.com
user @example.com
```

### Password Validation

```javascript
password.length >= 8
```

**Valid Examples:**
```
password123
MyP@ssw0rd
123456789
abcdefgh
```

**Invalid Examples:**
```
1234567      (7 characters)
short        (5 characters)
pass         (4 characters)
p            (1 character)
```

---

## Testing Tools Used

```bash
# Browser DevTools
- Console: Check for JavaScript errors
- Network: Verify API calls
- Storage: Check localStorage
- Responsive Design Mode: Test mobile

# Accessibility
- WAVE (WebAIM)
- axe DevTools
- NVDA Screen Reader
- Keyboard Navigation

# Performance
- Chrome DevTools Performance
- Lighthouse
- WebPageTest
```

---

## Bug Report Template

If issues are found during testing:

```markdown
### Title
[Brief description of the issue]

### Steps to Reproduce
1. ...
2. ...
3. ...

### Expected Result
[What should happen]

### Actual Result
[What actually happened]

### Screenshots
[Include if visual issue]

### Browser/Device
[Chrome 120 on Windows 11 / Safari on iPhone 14]

### Console Errors
[Copy any error messages from console]
```

---

End of Test Examples Document
