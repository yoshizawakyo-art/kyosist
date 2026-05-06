import base64
import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from .schemas.auth import TokenResponse

logger = logging.getLogger(__name__)

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, Content
except ImportError:
    SendGridAPIClient = None
    Mail = None
    Email = None
    Content = None


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440


def _get_jwt_secret_key() -> str:
    secret_key = os.environ.get("JWT_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured")
    return secret_key


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _get_jwt_secret_key(), algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, _get_jwt_secret_key(), algorithms=[ALGORITHM])


def authenticate_user(
    email: str, password: str, hashed_password: str
) -> TokenResponse | None:
    if not verify_password(password, hashed_password):
        return None

    access_token = create_access_token({"sub": email})
    return TokenResponse(access_token=access_token)


def generate_password_reset_token() -> str:
    """パスワードリセットトークンを生成（base64エンコード）"""
    token_bytes = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(token_bytes).decode("utf-8").rstrip("=")


def hash_reset_token(token: str) -> str:
    """リセットトークンを SHA256 でハッシュ化"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def send_password_reset_email(email: str, reset_token: str, reset_url: str) -> None:
    """パスワードリセットメールを SendGrid 経由で送信

    Args:
        email: 送信先メールアドレス
        reset_token: パスワードリセットトークン
        reset_url: パスワードリセットページの基底 URL

    Note:
        SendGrid API キーがない場合、またはメール送信に失敗した場合、
        ログに出力するが処理を続行します（ローカル開発での利便性を確保）。
    """
    if SendGridAPIClient is None:
        logger.warning(
            "SendGrid library not installed. Skipping password reset email to %s",
            email,
        )
        return

    api_key = os.environ.get("SENDGRID_API_KEY")
    from_email = os.environ.get("SENDGRID_FROM_EMAIL")

    if not api_key or not from_email:
        logger.warning(
            "SENDGRID_API_KEY or SENDGRID_FROM_EMAIL not configured. "
            "Skipping password reset email to %s",
            email,
        )
        return

    full_reset_url = f"{reset_url}?token={reset_token}"

    html_content = _build_password_reset_email_html(email, full_reset_url)

    try:
        sg = SendGridAPIClient(api_key)
        mail = Mail(
            from_email=Email(from_email),
            to_emails=Email(email),
            subject="パスワードリセットのご案内",
            html_content=Content("text/html", html_content),
        )
        sg.send(mail)
        logger.info("Password reset email sent to %s", email)
    except Exception as exc:
        logger.error(
            "Failed to send password reset email to %s: %s", email, exc, exc_info=True
        )


def _build_password_reset_email_html(email: str, reset_url: str) -> str:
    """パスワードリセットメールの HTML テンプレートを生成

    Args:
        email: 宛先メールアドレス
        reset_url: パスワードリセット用の完全 URL

    Returns:
        HTML 形式のメール本文
    """
    return f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #333;
            background-color: #f9fafb;
            margin: 0;
            padding: 0;
        }}
        .email-container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            padding: 40px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
            color: #111;
        }}
        .content {{
            margin-bottom: 30px;
            line-height: 1.6;
            color: #555;
        }}
        .content p {{
            margin: 10px 0;
        }}
        .reset-button {{
            display: inline-block;
            background-color: #3b82f6;
            color: #ffffff;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-weight: 600;
            margin: 20px 0;
        }}
        .reset-button:hover {{
            background-color: #2563eb;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 12px;
            color: #999;
            text-align: center;
        }}
        .warning {{
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 12px;
            margin: 20px 0;
            border-radius: 4px;
            font-size: 13px;
            color: #92400e;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>パスワードリセット</h1>
        </div>

        <div class="content">
            <p>お疲れさまです。</p>

            <p>パスワードリセットのリクエストを受け取りました。以下のボタンをクリックして新しいパスワードを設定してください。</p>

            <div style="text-align: center;">
                <a href="{reset_url}" class="reset-button">
                    パスワードをリセット
                </a>
            </div>

            <p>ボタンが表示されない場合は、以下の URL をコピーしてブラウザのアドレスバーに貼り付けてください：</p>
            <p style="word-break: break-all; background-color: #f3f4f6; padding: 10px; border-radius: 4px; font-size: 12px;">
                {reset_url}
            </p>

            <div class="warning">
                <strong>重要:</strong> このリンクの有効期限は 1 時間です。期限内にパスワードをリセットしてください。
            </div>

            <p>このメールに心当たりがない場合は、何もしないでください。パスワードは変更されません。</p>
        </div>

        <div class="footer">
            <p>このメールは自動送信です。返信はできません。</p>
            <p>Copyright © 2026 Kyosist. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
