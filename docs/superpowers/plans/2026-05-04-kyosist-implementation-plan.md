# Kyosist MVP 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase 1（認証）と Phase 2（チャット + スキル基本実行）を実装し、ユーザーがスキルを定義・実行できる MVP を完成させる。

**Architecture:** 
- 4層構成（認証 → チャット UI → AI エージェント → スキル実行エンジン）
- JWT ベースの認証、ユーザーごとのスキル隔離
- チャットを中心に、自然言語スキル定義・実行

**Tech Stack:** Python FastAPI、Supabase PostgreSQL、Vanilla JS、JWT、bcrypt

---

## **セットアップ・依存関係**

### Task 0: 依存ライブラリ追加

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: パスワード・トークン用ライブラリを追加**

`requirements.txt` の最後に以下を追加：
```
PyJWT==2.8.1
python-multipart==0.0.6
email-validator==2.1.0
```

- [ ] **Step 2: インストール確認**

Run: `pip install -r requirements.txt`
Expected: 新しいライブラリのインストール完了

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: 認証・メール用ライブラリを追加"
```

---

## **Phase 1: 認証基盤**

### Task 1-1: 認証テーブル設計・マイグレーション作成

**Files:**
- Create: `supabase/migrations/005_authentication.sql`

- [ ] **Step 1: マイグレーションファイルを作成**

`supabase/migrations/005_authentication.sql`:
```sql
-- users テーブル
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- password_reset_tokens テーブル
CREATE TABLE password_reset_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token VARCHAR(255) UNIQUE NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);
```

- [ ] **Step 2: Supabase にマイグレーション適用（ローカル確認）**

Supabase ダッシュボードで SQL を実行するか、Supabase CLI で：
```bash
supabase db push
```
Expected: テーブル作成完了

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/005_authentication.sql
git commit -m "feat: 認証テーブル（users, password_reset_tokens）を作成"
```

---

### Task 1-2: 認証サービスクラス（パスワードハッシュ・JWT）

**Files:**
- Create: `src/api/auth_service.py`

- [ ] **Step 1: auth_service.py を作成（ユーザー登録）**

```python
import os
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional
import bcrypt

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
RESET_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    """パスワードを bcrypt でハッシュ化"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """パスワードを検証"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: str) -> str:
    """JWT アクセストークンを生成"""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """JWT トークンを検証し、user_id を返す。無効ならNone。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_reset_token() -> str:
    """パスワードリセット用トークンを生成"""
    return secrets.token_urlsafe(32)
```

- [ ] **Step 2: テストファイルを作成（パスワードハッシュ検証）**

Create: `tests/test_auth_service.py`:
```python
import pytest
from src.api.auth_service import hash_password, verify_password, create_access_token, verify_token


def test_hash_password_and_verify():
    """パスワードハッシュ・検証が正常に機能"""
    password = "secure_password_123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_create_and_verify_token():
    """JWT トークン生成・検証が正常に機能"""
    user_id = "test-user-123"
    token = create_access_token(user_id)
    
    assert token is not None
    assert verify_token(token) == user_id


def test_verify_invalid_token():
    """無効なトークンは None を返す"""
    assert verify_token("invalid.token.here") is None
```

- [ ] **Step 3: テストを実行**

Run: `pytest tests/test_auth_service.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/api/auth_service.py tests/test_auth_service.py
git commit -m "feat: 認証サービス（パスワードハッシュ・JWT）を実装"
```

---

### Task 1-3: ログイン・サインアップ API エンドポイント

**Files:**
- Modify: `src/api/index.py`
- Create: `tests/test_auth_api.py`

- [ ] **Step 1: 認証 API エンドポイントを追加（テストファースト）**

Create: `tests/test_auth_api.py`:
```python
import pytest
from fastapi.testclient import TestClient
from src.api.index import app

client = TestClient(app)


def test_signup_success(db):
    """サインアップが成功し、ユーザーが作成される"""
    response = client.post("/api/auth/signup", json={
        "email": "user@example.com",
        "password": "secure_password_123"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
    assert "access_token" in data


def test_signup_duplicate_email(db):
    """既存メールでのサインアップは失敗"""
    # 1回目
    client.post("/api/auth/signup", json={
        "email": "user@example.com",
        "password": "secure_password_123"
    })
    
    # 2回目（失敗するはず）
    response = client.post("/api/auth/signup", json={
        "email": "user@example.com",
        "password": "another_password"
    })
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(db):
    """ログインが成功し、トークンが返される"""
    # ユーザーを先に作成
    client.post("/api/auth/signup", json={
        "email": "user@example.com",
        "password": "secure_password_123"
    })
    
    # ログイン
    response = client.post("/api/auth/login", json={
        "email": "user@example.com",
        "password": "secure_password_123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_invalid_credentials(db):
    """無効な認証情報でのログインは失敗"""
    response = client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrong_password"
    })
    
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]
```

- [ ] **Step 2: API エンドポイントを実装**

`src/api/index.py` に以下を追加：

```python
from fastapi import FastAPI, HTTPException, Depends, Form
from pydantic import BaseModel, EmailStr
from src.api.auth_service import (
    hash_password, verify_password, create_access_token, verify_token
)
import os
from supabase import create_client, Client

# Supabase クライアント初期化
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    email: str
    access_token: str


@app.post("/api/auth/signup", status_code=201, response_model=AuthResponse)
async def signup(request: SignupRequest):
    """ユーザー登録"""
    # メールの重複チェック
    existing = supabase.table("users").select("*").eq("email", request.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # パスワードをハッシュ化
    password_hash = hash_password(request.password)
    
    # ユーザーを作成
    user = supabase.table("users").insert({
        "email": request.email,
        "password_hash": password_hash
    }).execute()
    
    user_id = user.data[0]["id"]
    token = create_access_token(user_id)
    
    return AuthResponse(email=request.email, access_token=token)


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """ログイン"""
    # ユーザーを取得
    result = supabase.table("users").select("*").eq("email", request.email).execute()
    
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = result.data[0]
    
    # パスワードを検証
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # トークンを生成
    token = create_access_token(user["id"])
    
    return AuthResponse(email=request.email, access_token=token)
```

- [ ] **Step 3: テストを実行**

Run: `pytest tests/test_auth_api.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/api/index.py tests/test_auth_api.py
git commit -m "feat: ログイン・サインアップ API エンドポイント"
```

---

### Task 1-4: パスワードリセット API

**Files:**
- Modify: `src/api/index.py`
- Modify: `tests/test_auth_api.py`
- Modify: `src/api/auth_service.py`

- [ ] **Step 1: パスワードリセット API テストを追加**

`tests/test_auth_api.py` に追加：
```python
def test_request_password_reset(db):
    """パスワードリセット要求が成功"""
    # ユーザーを作成
    client.post("/api/auth/signup", json={
        "email": "user@example.com",
        "password": "secure_password_123"
    })
    
    # リセット要求
    response = client.post("/api/auth/request-password-reset", json={
        "email": "user@example.com"
    })
    
    assert response.status_code == 200
    assert "reset_sent" in response.json()


def test_reset_password_with_token(db):
    """トークンでパスワードリセットが成功"""
    # ユーザーを作成
    client.post("/api/auth/signup", json={
        "email": "user@example.com",
        "password": "secure_password_123"
    })
    
    # リセット要求
    reset_resp = client.post("/api/auth/request-password-reset", json={
        "email": "user@example.com"
    })
    
    # トークンを取得（テスト用。実際はDB から）
    # リセット実行
    response = client.post("/api/auth/reset-password", json={
        "token": "test-token-12345",
        "new_password": "new_secure_password_456"
    })
    
    assert response.status_code == 200
```

- [ ] **Step 2: パスワードリセット API を実装**

`src/api/index.py` に追加：
```python
from src.api.auth_service import generate_reset_token
from datetime import datetime, timedelta

class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@app.post("/api/auth/request-password-reset")
async def request_password_reset(request: RequestPasswordResetRequest):
    """パスワードリセット要求"""
    # ユーザーを取得
    result = supabase.table("users").select("*").eq("email", request.email).execute()
    
    if not result.data:
        # セキュリティ：ユーザーが存在しなくても「成功」を返す
        return {"reset_sent": True}
    
    user = result.data[0]
    
    # リセットトークンを生成
    reset_token = generate_reset_token()
    expires_at = (datetime.utcnow() + timedelta(minutes=60)).isoformat()
    
    supabase.table("password_reset_tokens").insert({
        "user_id": user["id"],
        "token": reset_token,
        "expires_at": expires_at
    }).execute()
    
    # メール送信（簡易版：実装時に外部メール API を使用）
    # send_reset_email(request.email, reset_token)
    
    return {"reset_sent": True}


@app.post("/api/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """パスワードをリセット"""
    # トークンを検証
    result = supabase.table("password_reset_tokens").select("*").eq("token", request.token).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    token_data = result.data[0]
    
    # 有効期限をチェック
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    if datetime.utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="Token has expired")
    
    # パスワードを更新
    user_id = token_data["user_id"]
    password_hash = hash_password(request.new_password)
    
    supabase.table("users").update({"password_hash": password_hash}).eq("id", user_id).execute()
    
    # トークンを削除
    supabase.table("password_reset_tokens").delete().eq("id", token_data["id"]).execute()
    
    return {"password_reset": True}
```

- [ ] **Step 3: テストを実行**

Run: `pytest tests/test_auth_api.py::test_request_password_reset -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/api/index.py tests/test_auth_api.py
git commit -m "feat: パスワードリセット API を実装"
```

---

### Task 1-5: ログイン画面 UI（HTML・JS）

**Files:**
- Create: `src/public/index.html`
- Create: `src/public/auth/login.html`
- Create: `src/public/auth/main.js`
- Create: `src/public/auth/style.css`
- Create: `src/public/common/auth.js`

- [ ] **Step 1: ランディング画面を作成**

Create: `src/public/index.html`:
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kyosist - スキル自動化</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f5f5; }
        .container { max-width: 600px; margin: 100px auto; text-align: center; padding: 20px; }
        h1 { font-size: 2.5em; margin-bottom: 20px; color: #333; }
        p { font-size: 1.1em; color: #666; margin-bottom: 30px; }
        .button-group { display: flex; gap: 10px; justify-content: center; }
        a { padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; cursor: pointer; }
        .btn-login { background: #2563eb; color: white; }
        .btn-signup { background: #fff; color: #2563eb; border: 2px solid #2563eb; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Kyosist</h1>
        <p>定型業務をスキル化して自動実行</p>
        <div class="button-group">
            <a href="/auth/login.html" class="btn-login">ログイン</a>
            <a href="/auth/signup.html" class="btn-signup">サインアップ</a>
        </div>
    </div>
</body>
</html>
```

- [ ] **Step 2: ログイン画面を作成**

Create: `src/public/auth/login.html`:
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ログイン - Kyosist</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="auth-container">
        <div class="auth-box">
            <h1>ログイン</h1>
            <form id="loginForm">
                <div class="form-group">
                    <label for="email">メール</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="password">パスワード</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="btn-primary">ログイン</button>
            </form>
            <p class="auth-link">
                アカウントがないですか？ <a href="signup.html">サインアップ</a>
            </p>
            <p class="auth-link">
                パスワードを忘れた？ <a href="reset-password.html">リセット</a>
            </p>
            <div id="errorMessage" class="error-message"></div>
        </div>
    </div>
    <script src="main.js"></script>
</body>
</html>
```

- [ ] **Step 3: 認証ヘルパークラスを作成**

Create: `src/public/common/auth.js`:
```javascript
class AuthHelper {
    constructor() {
        this.tokenKey = 'kyosist_token';
    }

    async login(email, password) {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'ログインに失敗しました');
        }

        const data = await response.json();
        this.setToken(data.access_token);
        return data;
    }

    async signup(email, password) {
        const response = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'サインアップに失敗しました');
        }

        const data = await response.json();
        this.setToken(data.access_token);
        return data;
    }

    setToken(token) {
        localStorage.setItem(this.tokenKey, token);
    }

    getToken() {
        return localStorage.getItem(this.tokenKey);
    }

    isAuthenticated() {
        return !!this.getToken();
    }

    logout() {
        localStorage.removeItem(this.tokenKey);
    }

    redirectIfNotAuthenticated() {
        if (!this.isAuthenticated()) {
            window.location.href = '/index.html';
        }
    }
}

const authHelper = new AuthHelper();
```

- [ ] **Step 4: ログイン画面のロジックを実装**

Create: `src/public/auth/main.js`:
```javascript
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('errorMessage');

    try {
        errorDiv.textContent = '';
        await authHelper.login(email, password);
        window.location.href = '/chat/index.html';
    } catch (error) {
        errorDiv.textContent = error.message;
    }
});
```

- [ ] **Step 5: スタイルを作成**

Create: `src/public/auth/style.css`:
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

.auth-container {
    width: 100%;
    max-width: 400px;
    padding: 20px;
}

.auth-box {
    background: white;
    border-radius: 12px;
    padding: 40px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

h1 {
    margin-bottom: 30px;
    color: #333;
    text-align: center;
}

.form-group {
    margin-bottom: 20px;
}

label {
    display: block;
    margin-bottom: 8px;
    color: #555;
    font-weight: 500;
}

input[type="email"],
input[type="password"] {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 1em;
}

input[type="email"]:focus,
input[type="password"]:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn-primary {
    width: 100%;
    padding: 12px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    cursor: pointer;
    margin-top: 10px;
}

.btn-primary:hover {
    background: #5568d3;
}

.auth-link {
    text-align: center;
    margin-top: 20px;
    color: #666;
}

.auth-link a {
    color: #667eea;
    text-decoration: none;
    font-weight: bold;
}

.auth-link a:hover {
    text-decoration: underline;
}

.error-message {
    margin-top: 15px;
    padding: 12px;
    background: #fee;
    color: #c33;
    border-radius: 6px;
    font-size: 0.9em;
}
```

- [ ] **Step 6: Commit**

```bash
git add src/public/index.html src/public/auth/ src/public/common/auth.js
git commit -m "feat: ログイン・サインアップ UI（HTML・JS・CSS）を実装"
```

---

### Task 1-6: サインアップ・パスワードリセット画面

**Files:**
- Create: `src/public/auth/signup.html`
- Create: `src/public/auth/reset-password.html`

- [ ] **Step 1: サインアップ画面を作成**

Create: `src/public/auth/signup.html`:
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>サインアップ - Kyosist</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="auth-container">
        <div class="auth-box">
            <h1>サインアップ</h1>
            <form id="signupForm">
                <div class="form-group">
                    <label for="email">メール</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="password">パスワード</label>
                    <input type="password" id="password" name="password" required>
                    <small style="color: #666; margin-top: 4px; display: block;">最低8文字推奨</small>
                </div>
                <div class="form-group">
                    <label for="confirmPassword">パスワード（確認）</label>
                    <input type="password" id="confirmPassword" name="confirmPassword" required>
                </div>
                <button type="submit" class="btn-primary">アカウント作成</button>
            </form>
            <p class="auth-link">
                既にアカウントをお持ちですか？ <a href="login.html">ログイン</a>
            </p>
            <div id="errorMessage" class="error-message"></div>
        </div>
    </div>
    <script src="../common/auth.js"></script>
    <script>
        document.getElementById('signupForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const errorDiv = document.getElementById('errorMessage');

            if (password !== confirmPassword) {
                errorDiv.textContent = 'パスワードが一致しません';
                return;
            }

            if (password.length < 8) {
                errorDiv.textContent = 'パスワードは最低8文字必要です';
                return;
            }

            try {
                errorDiv.textContent = '';
                await authHelper.signup(email, password);
                window.location.href = '/chat/index.html';
            } catch (error) {
                errorDiv.textContent = error.message;
            }
        });
    </script>
</body>
</html>
```

- [ ] **Step 2: パスワードリセット画面を作成**

Create: `src/public/auth/reset-password.html`:
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>パスワードリセット - Kyosist</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="auth-container">
        <div class="auth-box">
            <h1>パスワードリセット</h1>
            <p style="text-align: center; color: #666; margin-bottom: 20px; font-size: 0.9em;">
                登録済みのメールアドレスを入力すると、リセット用のリンクを送信します。
            </p>
            <form id="resetForm">
                <div class="form-group">
                    <label for="email">メール</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <button type="submit" class="btn-primary">リセットリンクを送信</button>
            </form>
            <p class="auth-link">
                <a href="login.html">ログイン画面に戻る</a>
            </p>
            <div id="successMessage" class="success-message" style="display: none;">
                リセットリンクを送信しました。メールをご確認ください。
            </div>
            <div id="errorMessage" class="error-message"></div>
        </div>
    </div>
    <script src="../common/auth.js"></script>
    <script>
        document.getElementById('resetForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const errorDiv = document.getElementById('errorMessage');
            const successDiv = document.getElementById('successMessage');

            try {
                errorDiv.textContent = '';
                successDiv.style.display = 'none';

                const response = await fetch('/api/auth/request-password-reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });

                if (!response.ok) {
                    throw new Error('リセット要求に失敗しました');
                }

                successDiv.style.display = 'block';
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 3000);
            } catch (error) {
                errorDiv.textContent = error.message;
            }
        });
    </script>
</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add src/public/auth/signup.html src/public/auth/reset-password.html
git commit -m "feat: サインアップ・パスワードリセット画面を実装"
```

---

## **Phase 2: チャット + スキル基本実行**

### Task 2-1: スキルテーブル設計・マイグレーション作成

**Files:**
- Create: `supabase/migrations/006_skills.sql`

- [ ] **Step 1: マイグレーションファイルを作成**

`supabase/migrations/006_skills.sql`:
```sql
-- skills テーブル
CREATE TABLE skills (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  operation_log JSONB DEFAULT '[]',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- skill_executions テーブル
CREATE TABLE skill_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status VARCHAR(50) DEFAULT 'pending',
  result_log JSONB DEFAULT '{}',
  executed_at TIMESTAMP,
  completed_at TIMESTAMP,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_skills_user_id ON skills(user_id);
CREATE INDEX idx_skill_executions_user_id ON skill_executions(user_id);
CREATE INDEX idx_skill_executions_skill_id ON skill_executions(skill_id);
CREATE INDEX idx_skill_executions_status ON skill_executions(status);
```

- [ ] **Step 2: Supabase にマイグレーション適用**

```bash
supabase db push
```
Expected: テーブル作成完了

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/006_skills.sql
git commit -m "feat: スキルテーブル（skills, skill_executions）を作成"
```

---

### Task 2-2: スキル実行サービス・API

**Files:**
- Create: `src/api/skill_service.py`
- Modify: `src/api/index.py`
- Create: `tests/test_skill_api.py`

- [ ] **Step 1: スキルサービスを実装（テストファースト）**

Create: `tests/test_skill_api.py`:
```python
import pytest
from fastapi.testclient import TestClient
from src.api.index import app

client = TestClient(app)


def test_create_skill(auth_headers):
    """スキルを作成"""
    response = client.post(
        "/api/skills",
        json={
            "name": "メール送信",
            "description": "毎日の定例メールを送信"
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "メール送信"
    assert "id" in data


def test_list_skills(auth_headers):
    """ユーザーのスキル一覧を取得"""
    # スキルを作成
    client.post(
        "/api/skills",
        json={"name": "スキル1", "description": "説明1"},
        headers=auth_headers
    )

    # 一覧取得
    response = client.get("/api/skills", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "スキル1"


def test_execute_skill(auth_headers):
    """スキルを実行"""
    # スキルを作成
    create_resp = client.post(
        "/api/skills",
        json={"name": "テストスキル", "description": "テスト説明"},
        headers=auth_headers
    )
    skill_id = create_resp.json()["id"]

    # スキルを実行
    response = client.post(
        f"/api/skills/{skill_id}/execute",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["pending", "running", "success", "failed"]
```

- [ ] **Step 2: スキルサービスを実装**

Create: `src/api/skill_service.py`:
```python
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
import os
from supabase import create_client, Client

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


class SkillRequest(BaseModel):
    name: str
    description: Optional[str] = None
    operation_log: Optional[dict] = None


class SkillResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: str


class ExecutionResponse(BaseModel):
    id: str
    skill_id: str
    status: str
    executed_at: Optional[str]


def create_skill(user_id: str, request: SkillRequest) -> dict:
    """スキルを作成"""
    result = supabase.table("skills").insert({
        "user_id": user_id,
        "name": request.name,
        "description": request.description,
        "operation_log": request.operation_log or []
    }).execute()

    return result.data[0]


def list_skills(user_id: str) -> list:
    """ユーザーのスキル一覧を取得"""
    result = supabase.table("skills").select("*").eq("user_id", user_id).execute()
    return result.data


def delete_skill(user_id: str, skill_id: str) -> bool:
    """スキルを削除"""
    supabase.table("skills").delete().eq("id", skill_id).eq("user_id", user_id).execute()
    return True


def execute_skill(user_id: str, skill_id: str) -> dict:
    """スキルを実行"""
    # スキルが存在するか確認
    skill_result = supabase.table("skills").select("*").eq("id", skill_id).eq("user_id", user_id).execute()
    if not skill_result.data:
        raise ValueError("Skill not found")

    skill = skill_result.data[0]

    # 実行レコードを作成
    execution = supabase.table("skill_executions").insert({
        "skill_id": skill_id,
        "user_id": user_id,
        "status": "running",
        "executed_at": datetime.utcnow().isoformat()
    }).execute()

    execution_id = execution.data[0]["id"]

    # スキル実行ロジック（簡易版）
    try:
        # 実装予定：operation_log に基づいて操作を再現
        result_log = {"executed_operations": len(skill.get("operation_log", []))}

        # 実行結果を更新
        supabase.table("skill_executions").update({
            "status": "success",
            "result_log": result_log,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", execution_id).execute()

    except Exception as e:
        # エラー時は失敗状態に更新
        supabase.table("skill_executions").update({
            "status": "failed",
            "error_message": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", execution_id).execute()

    return execution.data[0]
```

- [ ] **Step 3: API エンドポイントを追加**

`src/api/index.py` に追加：
```python
from src.api.skill_service import create_skill, list_skills, delete_skill, execute_skill
from fastapi import Header

def get_current_user(authorization: str = Header(None)) -> str:
    """JWT トークンから user_id を取得"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.replace("Bearer ", "")
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


@app.post("/api/skills", status_code=201)
async def create_skill_endpoint(request: SkillRequest, user_id: str = Depends(get_current_user)):
    """スキルを作成"""
    skill = create_skill(user_id, request)
    return skill


@app.get("/api/skills")
async def list_skills_endpoint(user_id: str = Depends(get_current_user)):
    """ユーザーのスキル一覧を取得"""
    skills = list_skills(user_id)
    return skills


@app.delete("/api/skills/{skill_id}")
async def delete_skill_endpoint(skill_id: str, user_id: str = Depends(get_current_user)):
    """スキルを削除"""
    delete_skill(user_id, skill_id)
    return {"deleted": True}


@app.post("/api/skills/{skill_id}/execute")
async def execute_skill_endpoint(skill_id: str, user_id: str = Depends(get_current_user)):
    """スキルを実行"""
    execution = execute_skill(user_id, skill_id)
    return execution
```

- [ ] **Step 4: テストを実行**

Run: `pytest tests/test_skill_api.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/api/skill_service.py src/api/index.py tests/test_skill_api.py
git commit -m "feat: スキル実行 API（作成・一覧・削除・実行）"
```

---

### Task 2-3: AI エージェント統合（自然言語 → スキル実行）

**Files:**
- Modify: `src/api/agent_service.py`
- Modify: `src/api/index.py`

- [ ] **Step 1: AI エージェント統合ロジックを実装**

Modify: `src/api/agent_service.py`:
```python
from src.api.skill_service import list_skills, execute_skill


async def process_skill_command(user_id: str, user_message: str) -> dict:
    """
    ユーザーメッセージを解析し、スキル実行指示に変換
    例：「メール送信スキルを実行して」→ スキル ID を特定して実行
    """
    user_skills = list_skills(user_id)

    # 簡易的な自然言語解析：スキル名がメッセージに含まれているか確認
    for skill in user_skills:
        if skill["name"].lower() in user_message.lower():
            # スキルを実行
            execution = execute_skill(user_id, skill["id"])
            return {
                "type": "skill_execution",
                "skill_name": skill["name"],
                "execution_id": execution["id"],
                "status": execution["status"],
                "message": f"'{skill['name']}' スキルを実行しています..."
            }

    # スキルが見つからない場合
    return {
        "type": "info",
        "message": "申し訳ありません。該当するスキルが見つかりません。"
    }


async def generate_response(user_id: str, user_message: str) -> dict:
    """ユーザーメッセージに応答"""
    # スキル実行コマンドかどうか判定
    if any(keyword in user_message.lower() for keyword in ["実行", "してください", "して"]):
        return await process_skill_command(user_id, user_message)

    # 通常の応答
    return {
        "type": "info",
        "message": "スキルを実行するには、スキル名を含めて「〇〇スキルを実行して」と入力してください。"
    }
```

- [ ] **Step 2: チャット API にエージェント統合を追加**

`src/api/index.py` に追加：
```python
from src.api.agent_service import generate_response


class ChatMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    type: str
    message: str
    execution_id: str = None


@app.post("/api/chat/message")
async def chat_message(request: ChatMessageRequest, user_id: str = Depends(get_current_user)):
    """チャットメッセージを処理"""
    response = await generate_response(user_id, request.message)
    return response
```

- [ ] **Step 3: Commit**

```bash
git add src/api/agent_service.py src/api/index.py
git commit -m "feat: AI エージェント統合（自然言語 → スキル実行指示）"
```

---

### Task 2-4: チャット画面 UI（認証後）

**Files:**
- Modify: `src/public/chat/index.html`
- Modify: `src/public/chat/main.js`

- [ ] **Step 1: チャット画面を実装**

Modify: `src/public/chat/index.html`:
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>チャット - Kyosist</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>Kyosist</h1>
            <button id="logoutBtn" class="logout-btn">ログアウト</button>
        </div>

        <div class="chat-main">
            <div id="messageList" class="message-list"></div>
        </div>

        <div class="chat-input-area">
            <form id="messageForm">
                <input type="text" id="messageInput" placeholder="スキルを実行するか、質問してください..." required>
                <button type="submit" class="send-btn">送信</button>
            </form>
        </div>
    </div>

    <script src="../common/auth.js"></script>
    <script src="main.js"></script>
</body>
</html>
```

- [ ] **Step 2: チャット画面のロジックを実装**

Modify: `src/public/chat/main.js`:
```javascript
// 認証確認
authHelper.redirectIfNotAuthenticated();

const messageList = document.getElementById('messageList');
const messageForm = document.getElementById('messageForm');
const messageInput = document.getElementById('messageInput');
const logoutBtn = document.getElementById('logoutBtn');

// メッセージを UI に追加
function addMessage(text, isUser) {
    const messageDiv = document.createElement('div');
    messageDiv.className = isUser ? 'message user-message' : 'message ai-message';
    messageDiv.textContent = text;
    messageList.appendChild(messageDiv);
    messageList.scrollTop = messageList.scrollHeight;
}

// メッセージを送信
messageForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = messageInput.value.trim();
    if (!message) return;

    // ユーザーメッセージを表示
    addMessage(message, true);
    messageInput.value = '';

    try {
        // API にメッセージを送信
        const response = await fetch('/api/chat/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authHelper.getToken()}`
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            throw new Error('メッセージの送信に失敗しました');
        }

        const data = await response.json();
        addMessage(data.message, false);
    } catch (error) {
        addMessage(`エラー: ${error.message}`, false);
    }
});

// ログアウト
logoutBtn.addEventListener('click', () => {
    authHelper.logout();
    window.location.href = '/index.html';
});
```

- [ ] **Step 3: スタイルを更新**

`src/public/chat/style.css`:
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #f5f5f5;
}

.chat-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 800px;
    margin: 0 auto;
    background: white;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
}

.chat-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-header h1 {
    font-size: 1.5em;
}

.logout-btn {
    padding: 8px 16px;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: 1px solid white;
    border-radius: 6px;
    cursor: pointer;
}

.logout-btn:hover {
    background: rgba(255, 255, 255, 0.3);
}

.chat-main {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.message-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.message {
    padding: 12px 16px;
    border-radius: 8px;
    max-width: 70%;
}

.user-message {
    background: #667eea;
    color: white;
    align-self: flex-end;
}

.ai-message {
    background: #e5e5e5;
    color: #333;
    align-self: flex-start;
}

.chat-input-area {
    padding: 20px;
    border-top: 1px solid #ddd;
}

#messageForm {
    display: flex;
    gap: 10px;
}

#messageInput {
    flex: 1;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 1em;
}

#messageInput:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.send-btn {
    padding: 12px 24px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    cursor: pointer;
}

.send-btn:hover {
    background: #5568d3;
}
```

- [ ] **Step 4: Commit**

```bash
git add src/public/chat/
git commit -m "feat: チャット画面 UI（認証後）を実装"
```

---

### Task 2-5: スキル一覧・管理 UI

**Files:**
- Create: `src/public/skills/index.html`
- Create: `src/public/skills/main.js`
- Create: `src/public/skills/style.css`

- [ ] **Step 1: スキル一覧画面を作成**

Create: `src/public/skills/index.html`:
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>スキル管理 - Kyosist</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="skills-container">
        <div class="header">
            <h1>スキル管理</h1>
            <button id="createSkillBtn" class="btn-primary">新規スキル</button>
        </div>

        <div id="skillsList" class="skills-list"></div>

        <!-- 新規スキル作成モーダル -->
        <div id="createModal" class="modal" style="display: none;">
            <div class="modal-content">
                <span class="close">&times;</span>
                <h2>新規スキル作成</h2>
                <form id="createSkillForm">
                    <div class="form-group">
                        <label for="skillName">スキル名</label>
                        <input type="text" id="skillName" required>
                    </div>
                    <div class="form-group">
                        <label for="skillDesc">説明</label>
                        <textarea id="skillDesc" rows="4"></textarea>
                    </div>
                    <button type="submit" class="btn-primary">作成</button>
                </form>
            </div>
        </div>
    </div>

    <script src="../common/auth.js"></script>
    <script src="main.js"></script>
</body>
</html>
```

- [ ] **Step 2: スキル管理ロジックを実装**

Create: `src/public/skills/main.js`:
```javascript
authHelper.redirectIfNotAuthenticated();

const skillsList = document.getElementById('skillsList');
const createSkillBtn = document.getElementById('createSkillBtn');
const createModal = document.getElementById('createModal');
const createSkillForm = document.getElementById('createSkillForm');
const closeBtn = document.querySelector('.close');

// スキル一覧を読み込む
async function loadSkills() {
    try {
        const response = await fetch('/api/skills', {
            headers: { 'Authorization': `Bearer ${authHelper.getToken()}` }
        });

        if (!response.ok) throw new Error('スキル一覧の読み込みに失敗');

        const skills = await response.json();
        displaySkills(skills);
    } catch (error) {
        skillsList.innerHTML = `<p style="color: red;">${error.message}</p>`;
    }
}

// スキルを UI に表示
function displaySkills(skills) {
    skillsList.innerHTML = '';
    if (skills.length === 0) {
        skillsList.innerHTML = '<p>スキルがまだ作成されていません。</p>';
        return;
    }

    skills.forEach(skill => {
        const skillDiv = document.createElement('div');
        skillDiv.className = 'skill-card';
        skillDiv.innerHTML = `
            <h3>${skill.name}</h3>
            <p>${skill.description || '説明なし'}</p>
            <div class="skill-actions">
                <button class="btn-execute" data-id="${skill.id}">実行</button>
                <button class="btn-delete" data-id="${skill.id}">削除</button>
            </div>
        `;
        skillsList.appendChild(skillDiv);
    });

    // イベント委譲：実行ボタン
    skillsList.addEventListener('click', async (e) => {
        if (e.target.classList.contains('btn-execute')) {
            const skillId = e.target.dataset.id;
            await executeSkill(skillId);
        }
        if (e.target.classList.contains('btn-delete')) {
            const skillId = e.target.dataset.id;
            await deleteSkill(skillId);
        }
    });
}

// スキルを実行
async function executeSkill(skillId) {
    try {
        const response = await fetch(`/api/skills/${skillId}/execute`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authHelper.getToken()}` }
        });

        if (!response.ok) throw new Error('スキル実行に失敗');

        alert('スキルを実行しました');
        loadSkills();
    } catch (error) {
        alert(`エラー: ${error.message}`);
    }
}

// スキルを削除
async function deleteSkill(skillId) {
    if (!confirm('このスキルを削除しますか？')) return;

    try {
        const response = await fetch(`/api/skills/${skillId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authHelper.getToken()}` }
        });

        if (!response.ok) throw new Error('スキル削除に失敗');

        alert('スキルを削除しました');
        loadSkills();
    } catch (error) {
        alert(`エラー: ${error.message}`);
    }
}

// 新規スキル作成フォーム
createSkillBtn.addEventListener('click', () => {
    createModal.style.display = 'block';
});

closeBtn.addEventListener('click', () => {
    createModal.style.display = 'none';
});

createSkillForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('skillName').value;
    const description = document.getElementById('skillDesc').value;

    try {
        const response = await fetch('/api/skills', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authHelper.getToken()}`
            },
            body: JSON.stringify({ name, description })
        });

        if (!response.ok) throw new Error('スキル作成に失敗');

        alert('スキルを作成しました');
        createModal.style.display = 'none';
        createSkillForm.reset();
        loadSkills();
    } catch (error) {
        alert(`エラー: ${error.message}`);
    }
});

// ページロード時にスキル一覧を読み込む
loadSkills();
```

- [ ] **Step 3: スタイルを作成**

Create: `src/public/skills/style.css`:
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #f5f5f5;
    padding: 20px;
}

.skills-container {
    max-width: 900px;
    margin: 0 auto;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
}

.header h1 {
    font-size: 2em;
    color: #333;
}

.btn-primary {
    padding: 12px 24px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    cursor: pointer;
}

.btn-primary:hover {
    background: #5568d3;
}

.skills-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.skill-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.skill-card h3 {
    margin-bottom: 10px;
    color: #333;
}

.skill-card p {
    color: #666;
    margin-bottom: 15px;
    font-size: 0.9em;
}

.skill-actions {
    display: flex;
    gap: 10px;
}

.btn-execute,
.btn-delete {
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: bold;
}

.btn-execute {
    background: #2563eb;
    color: white;
}

.btn-execute:hover {
    background: #1d4ed8;
}

.btn-delete {
    background: #f43f5e;
    color: white;
}

.btn-delete:hover {
    background: #e11d48;
}

/* モーダル */
.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    padding: 30px;
    border-radius: 12px;
    max-width: 500px;
    width: 90%;
    position: relative;
}

.close {
    position: absolute;
    top: 15px;
    right: 20px;
    font-size: 2em;
    cursor: pointer;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    color: #555;
    font-weight: 500;
}

.form-group input,
.form-group textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 1em;
}

.form-group input:focus,
.form-group textarea:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}
```

- [ ] **Step 4: Commit**

```bash
git add src/public/skills/
git commit -m "feat: スキル一覧・管理 UI を実装"
```

---

## **MVP テスト・最終確認**

### Task 3: エンドツーエンド テスト（Playwright）

**Files:**
- Create: `my-playwright-project/tests/e2e.spec.ts`

- [ ] **Step 1: E2E テスト（ログイン → スキル実行）を作成**

Create: `my-playwright-project/tests/e2e.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';

test.describe('Kyosist MVP E2E', () => {
    const baseURL = 'http://localhost:8000';

    test('ユーザー登録 → ログイン → スキル作成 → 実行', async ({ page }) => {
        // ランディングページにアクセス
        await page.goto(`${baseURL}/index.html`);
        expect(await page.title()).toContain('Kyosist');

        // サインアップページへ移動
        await page.click('text=サインアップ');
        await page.fill('#email', `user-${Date.now()}@example.com`);
        await page.fill('#password', 'SecurePassword123');
        await page.fill('#confirmPassword', 'SecurePassword123');
        await page.click('button[type="submit"]');

        // チャット画面に遷移
        await page.waitForNavigation();
        expect(page.url()).toContain('/chat/');

        // スキル管理ページへ移動
        await page.goto(`${baseURL}/skills/index.html`);

        // スキル作成
        await page.click('text=新規スキル');
        await page.fill('#skillName', 'テストスキル');
        await page.fill('#skillDesc', 'テスト用のスキルです');
        await page.click('text=作成');

        // スキルが表示されるまで待機
        await page.waitForSelector('text=テストスキル');

        // スキル実行
        await page.click('text=実行');
        await page.waitForSelector('text=スキルを実行しました');
    });
});
```

- [ ] **Step 2: Playwright テストを実行**

Run: `cd my-playwright-project && npx playwright test --headed`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add my-playwright-project/tests/
git commit -m "test: MVP E2E テスト（ログイン → スキル実行）"
```

---

## **最終確認・品質チェック**

### Task 4: コード品質チェック

- [ ] **Step 1: リントチェック**

Run: `ruff check .`
Expected: No errors

- [ ] **Step 2: フォーマット確認**

Run: `ruff format --check .`
Expected: No errors

- [ ] **Step 3: すべてのテストを実行**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "chore: コード品質チェック完了（ruff, pytest）"
```

---

## **実行方法選択**

**Plan 完成・提示準備完了。**

### 実行方法選択（以下のどちらか）：

1. **Subagent-Driven（推奨）** — 1 Task ごとに fresh subagent を dispatch → レビュー → 進行
2. **Inline Execution** — このセッションで executing-plans を使って順次実行

**どちらで進めますか？**
