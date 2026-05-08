"""
=============================================================================
Kyosist AI チャットシステム - バックエンドAPI
=============================================================================

【概要】
このモジュールはFastAPIで実装されたバックエンドサーバーです。
フロントエンドからのチャットリクエストを受け取り、会話履歴を Supabase
データベースに保存し、AI応答を返却する REST API です。

【主な機能】
  - /api/conversations
    → 新規会話の作成、会話一覧の取得
  - /api/conversations/{conversation_id}/messages
    → 指定会話のメッセージ一覧取得
  - /api/chat
    → ユーザーメッセージの受信・AI応答の生成・保存
  - 静的ファイル配信（HTML/JS/CSS）

【必要な環境変数】
  - SUPABASE_URL: Supabase プロジェクトの API URL
  - SUPABASE_ANON_KEY: Supabase の公開 API キー（匿名クライアント用）

=============================================================================
"""

import asyncio
import hashlib
import ipaddress
import json
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from urllib.parse import urlparse

import jwt
import google.generativeai as genai
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from postgrest.exceptions import APIError
from pydantic import BaseModel, EmailStr, Field, field_validator
from supabase import Client, create_client

try:
    import bcrypt
except ImportError:  # pragma: no cover - handled at runtime with a clear API error
    bcrypt = None

from api import automation_service
from api.agent_service import (
    build_agent_event,
    create_gemini_client,
    generate_gemini_text,
    run_agent,
    stream_gemini_text,
)

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
MAX_CHAT_CONTEXT_MESSAGES = 30
CHAT_SYSTEM_PROMPT = """\
あなたは「Kyosist（キョシスト）」というAIアシスタントです。
以下のルールに従って応答してください。

- 常に日本語で応答する
- 簡潔で分かりやすい表現を使う
- ユーザーに寄り添う親切なトーンで答える
- 業務整理、調査、文章作成、実装相談を実務的に支援する
- 不確かな情報は断定せず、「確認が必要です」と伝える
""".strip()


def _get_jwt_secret_key() -> str:
    logger.info("retrieving JWT secret key from environment")
    secret_key = os.environ.get("JWT_SECRET_KEY")
    if not secret_key:
        logger.error("JWT_SECRET_KEY environment variable is NOT SET")
        raise HTTPException(
            status_code=500,
            detail="JWT secret key is not configured",
        )
    logger.info("JWT_SECRET_KEY found successfully")
    return secret_key


def _get_cors_allow_origins() -> list[str]:
    configured_origins = os.environ.get("CORS_ALLOW_ORIGINS", "")
    origins = [
        origin.strip() for origin in configured_origins.split(",") if origin.strip()
    ]
    return origins or ["http://localhost:8000"]


# FastAPI アプリケーションインスタンスを作成
app = FastAPI()

# ────────────────────────────────────────────────────────────────────────
# CORS（Cross-Origin Resource Sharing）設定
# ────────────────────────────────────────────────────────────────────────
# 目的: フロントエンドから異なるオリジン（ドメイン）からのリクエストを許可
# 設定内容:
#   - allow_origins: CORS_ALLOW_ORIGINS に指定されたオリジンを許可
#   - allow_methods=["*"] : すべてのHTTPメソッド(GET,POST,PUT等)を許可
#   - allow_headers=["*"] : すべてのリクエストヘッダーを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_allow_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════════════════
# データモデル定義（Pydantic）
# ════════════════════════════════════════════════════════════════════════
# 注: Pydantic は リクエスト/レスポンスのデータバリデーション・シリアライズに
#     使用されます。FastAPI により自動的にバリデーションとOpenAPI ドキュメント
#     生成が行われます。


class ChatRequest(BaseModel):
    """
    【チャットAPI のリクエストボディモデル】
    ユーザーがメッセージを送信する際のデータ構造を定義します。

    属性:
      message: str
        → ユーザーの入力テキスト（必須）。質問や指示内容など。
      conversation_id: Optional[uuid.UUID]
        → どの会話スレッドに属するかを指定するID（任意）。
        → None の場合：新規会話として扱われます。
        → UUID を指定：既存会話に新メッセージを追加します。
    """

    message: str
    conversation_id: Optional[uuid.UUID] = None


class ConversationResponse(BaseModel):
    """
    【会話（Conversation）のレスポンスモデル】
    会話の基本情報をクライアントに返却する際のデータ構造です。

    属性:
      id: uuid.UUID
        → 会話の一意識別子（主キー）。
      title: str
        → 会話のタイトル。通常は最初のユーザーメッセージから自動生成。
      created_at: str
        → 会話作成日時（ISO 8601 形式）。
      updated_at: str
        → 最後にメッセージが追加された日時（ISO 8601 形式）。
                 新しい会話ほど最初に表示されるようソートに使用。
    """

    id: uuid.UUID
    title: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    """
    【メッセージ（Message）のレスポンスモデル】
    会話内の個別メッセージ情報をクライアントに返却する際のデータ構造です。

    属性:
      id: uuid.UUID
        → メッセージの一意識別子（主キー）。
      conversation_id: uuid.UUID
        → このメッセージが属する会話ID。
      role: str
        → メッセージの送信者種別。"user" または "bot"。
      content: str
        → メッセージの本文テキスト。
      created_at: str
        → メッセージ作成日時（ISO 8601 形式）。
    """

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    created_at: str


class ChatResponse(BaseModel):
    """
    【チャットAPI のレスポンスモデル】
    /api/chat エンドポイントがAI応答を返却する際のデータ構造です。

    属性:
      reply: str
        → AI が生成した応答テキスト。
      conversation_id: uuid.UUID
        → このやり取りが属する会話ID。
        → 新規会話の場合：このレスポンスで初めて会話IDが通知されます。
    """

    reply: str
    conversation_id: uuid.UUID


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class AuthUserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LoginResponse(BaseModel):
    token: str
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: AuthUserResponse


class LogoutResponse(BaseModel):
    success: bool


class SkillCreate(BaseModel):
    """
    【スキル作成リクエストモデル】
    POST /api/skills エンドポイントで受け取るデータ構造です。

    属性:
      name: str
        → スキルの識別名。エージェントが skill_call(name, ...) で参照する。
      description: str
        → スキルの説明。エージェントがどのスキルを使うべきか判断する際に使用。
      action_url: str
        → Webhook の呼び出し先 URL。
      action_method: str
        → HTTP メソッド。"GET" または "POST"（デフォルト: "POST"）。
      action_body_template: str
        → リクエストボディのテンプレート。"{input}" がユーザー入力に置換される。
    """

    name: str
    description: str
    action_url: str
    action_method: Literal["GET", "POST"] = "POST"
    action_body_template: str = ""

    @field_validator("action_url")
    @classmethod
    def validate_action_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                "action_url は http:// または https:// で始まる必要があります"
            )
        hostname = parsed.hostname or ""
        blocked = ("localhost", "127.", "169.254.", "10.", "192.168.", "::1")
        if any(hostname == b or hostname.startswith(b) for b in blocked):
            raise ValueError("内部ネットワークへの URL は登録できません")
        return v


class SkillResponse(BaseModel):
    """
    【スキルレスポンスモデル】
    スキル取得・作成エンドポイントが返却するデータ構造です。

    属性:
      id: str         → スキルの UUID（文字列形式）
      name: str       → スキル識別名
      description: str → スキルの説明
      action_url: str  → Webhook URL
      action_method: str → HTTP メソッド
      action_body_template: str → ボディテンプレート
      created_at: str → 作成日時（ISO 8601 形式）
    """

    id: str
    name: str
    description: str
    action_url: str
    action_method: str
    action_body_template: str
    created_at: str


class SkillAssistantRequest(BaseModel):
    """AI スキル設計アシスタントへのリクエストモデル。"""

    message: str
    history: list[dict] = Field(default_factory=list)


class SkillAssistantResponse(BaseModel):
    """AI スキル設計アシスタントのレスポンスモデル。"""

    reply: str
    draft: Optional[SkillCreate] = None


class AutomationTaskCreate(BaseModel):
    """業務自動化タスク設定の作成リクエスト。"""

    task_name: str = Field(..., min_length=1)
    target_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    template_path: str = Field(..., min_length=1)
    output_directory: str = Field(..., min_length=1)
    output_filename_policy: str = "template_month"
    blocked_sites: list[str] = Field(default_factory=list)
    require_login_confirmation: bool = True
    require_regeneration_approval: bool = True


class AutomationTaskResponse(BaseModel):
    """業務自動化タスク設定のレスポンス。"""

    id: str
    name: str
    description: str = ""
    template_path: Optional[str] = None
    output_directory: Optional[str] = None
    filename_policy: dict = Field(default_factory=dict)
    approval_policy: dict = Field(default_factory=dict)
    blocked_site_rules: list = Field(default_factory=list)
    is_active: bool = True
    created_at: str
    updated_at: str


class AutomationRunCreate(BaseModel):
    """業務自動化タスク実行の作成リクエスト。"""

    task_id: str
    target_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    skill_id: Optional[str] = None
    require_regeneration_approval: bool = True
    approved_regeneration: bool = False


class AutomationRunResponse(BaseModel):
    """業務自動化タスク実行履歴のレスポンス。"""

    id: str
    task_id: str
    skill_id: Optional[str] = None
    target_month: str
    status: str
    current_step_id: Optional[str] = None
    resume_state_json: dict = Field(default_factory=dict)
    output_file_path: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: str
    updated_at: str


class AutomationLogCreate(BaseModel):
    """業務自動化実行ログの作成リクエスト。"""

    run_id: str
    level: Literal["debug", "info", "warning", "error"] = "info"
    message: str = Field(..., min_length=1)
    user_action_message: Optional[str] = None
    details_json: dict = Field(default_factory=dict)


class AutomationLogResponse(BaseModel):
    """業務自動化実行ログのレスポンス。"""

    id: str
    run_id: str
    step_id: Optional[str] = None
    level: str
    message: str
    user_action_message: Optional[str] = None
    details_json: dict = Field(default_factory=dict)
    created_at: str


class AutomationSiteCreate(BaseModel):
    """自動化対象サイトの作成リクエスト。"""

    name: str = Field(..., min_length=1)
    category: str = "business"
    base_url: Optional[str] = None
    allowed_domains: list[str] = Field(default_factory=list)
    blocked_site_rules: list = Field(default_factory=list)


class AutomationSiteResponse(BaseModel):
    """自動化対象サイトのレスポンス。"""

    id: str
    name: str
    category: str
    base_url: Optional[str] = None
    allowed_domains: list = Field(default_factory=list)
    blocked_site_rules: list = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)
    created_at: str
    updated_at: str


class SiteCredentialCreate(BaseModel):
    """サイト認証情報の作成リクエスト。"""

    site_id: str
    account_identifier: str = Field(..., min_length=1)
    secret: str = Field(..., min_length=1)
    metadata_json: dict = Field(default_factory=dict)


class SiteCredentialResponse(BaseModel):
    """サイト認証情報のレスポンス。秘密情報は返さない。"""

    id: str
    site_id: str
    account_identifier: str
    encryption_version: int
    key_id: str
    metadata_json: dict = Field(default_factory=dict)
    last_verified_at: Optional[str] = None
    created_at: str
    updated_at: str


class GeneratedFileResponse(BaseModel):
    """生成ファイル情報のレスポンス。"""

    id: str
    run_id: str
    task_id: str
    target_month: str
    file_path: str
    file_name: str
    template_path: Optional[str] = None
    file_kind: str = "excel"
    metadata_json: dict = Field(default_factory=dict)
    created_at: str


# ════════════════════════════════════════════════════════════════════════
# Supabase クライアント管理
# ════════════════════════════════════════════════════════════════════════
# 注: Supabase はバックエンド as a Service（BaaS）で、PostgreSQL データベース
#     と認証機能を提供します。


def get_supabase_client() -> Client:
    """
    【Supabase クライアント生成関数】
    環境変数からSupabaseの接続情報を読み込み、認証済みクライアントを返却します。
    呼び出すたびに新しいクライアントインスタンスが生成されます。

    戻り値:
      Client : Supabase ライブラリの Client インスタンス。
               このオブジェクトを通じてデータベーステーブルにアクセスします。

    環境変数:
      SUPABASE_URL: Supabase プロジェクトの API エンドポイント URL
      SUPABASE_ANON_KEY: 公開 API キー（認証なしのクライアント用）

    例外:
      KeyError: 環境変数が設定されていない場合に発生。
    """
    logger.info("initializing Supabase client")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    logger.info("Supabase URL env var: %s", "SET" if url else "NOT SET")
    logger.info("Supabase ANON_KEY env var: %s", "SET" if key else "NOT SET")
    if not url or not key:
        logger.error("Supabase configuration is missing: url=%s, key=%s", bool(url), bool(key))
        raise HTTPException(
            status_code=503,
            detail="データベース接続設定が不足しています。管理者に連絡してください。",
        )

    # 取得した認証情報でクライアントを生成・返却
    try:
        logger.info("creating Supabase client instance")
        client = create_client(url, key)
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as exc:
        logger.error("Supabase client creation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="データベースに接続できません。しばらくしてから再度お試しください。",
        ) from exc


def _fetch_user_by_email(client: Client, email: str) -> Optional[dict]:
    logger.info("checking if email already exists: %s", email)
    try:
        result = (
            client.table("users")
            .select("id,email,password_hash,created_at,updated_at")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        if not result.data:
            logger.info("email not found in database")
            return None
        logger.info("email found in database")
        return result.data[0]
    except Exception as exc:
        logger.error("failed to fetch user by email: %s", exc, exc_info=True)
        raise


def _fetch_user_by_id(client: Client, user_id: str) -> Optional[dict]:
    result = (
        client.table("users")
        .select("id,email,created_at,updated_at")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    return result.data[0]


def _verify_password(password: str, password_hash: str) -> bool:
    if bcrypt is None:
        raise HTTPException(
            status_code=500,
            detail="bcrypt dependency is not installed",
        )

    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _hash_password(password: str) -> str:
    logger.info("hashing password with bcrypt")
    if bcrypt is None:
        logger.error("bcrypt module is not installed")
        raise HTTPException(
            status_code=500,
            detail="bcrypt dependency is not installed",
        )

    try:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        logger.info("password hashed successfully")
        return hashed
    except Exception as exc:
        logger.error("password hashing failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="password hashing failed") from exc


def _insert_user(client: Client, email: str, password_hash: str) -> dict:
    logger.info("attempting to insert user: %s", email)
    try:
        result = (
            client.table("users")
            .insert({"email": email, "password_hash": password_hash})
            .execute()
        )
        if not result.data:
            logger.error("insert returned no data")
            raise ValueError("Failed to create user")
        user_id = result.data[0].get("id")
        logger.info("user inserted successfully: user_id=%s", user_id)
        return result.data[0]
    except Exception as exc:
        logger.error("failed to insert user: %s", exc, exc_info=True)
        raise


def _is_unique_constraint_violation(exc: Exception) -> bool:
    if isinstance(exc, APIError):
        values = (exc.code, exc.message, exc.details)
        return any(
            value
            and (
                value == "23505"
                or "duplicate key value violates unique constraint" in value.lower()
            )
            for value in values
        )
    return False


def _create_access_token(user_id: str) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "jti": secrets.token_urlsafe(16),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, _get_jwt_secret_key(), algorithm=JWT_ALGORITHM)
    return token, expires_at


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _request_ip_address(request: Request) -> Optional[str]:
    if request.client is None:
        return None
    host = request.client.host
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return None
    return host


def _insert_session(
    client: Client,
    user_id: str,
    token: str,
    expires_at: datetime,
    user_agent: Optional[str],
    ip_address: Optional[str],
) -> None:
    client.table("sessions").insert(
        {
            "user_id": user_id,
            "token_hash": _token_hash(token),
            "user_agent": user_agent,
            "ip_address": ip_address,
            "expires_at": expires_at.isoformat(),
        }
    ).execute()


def _fetch_active_session_by_token(client: Client, token: str) -> Optional[dict]:
    result = (
        client.table("sessions")
        .select("*")
        .eq("token_hash", _token_hash(token))
        .is_("revoked_at", "null")
        .gt("expires_at", datetime.now(timezone.utc).isoformat())
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    return result.data[0]


def _touch_session(client: Client, session_id: str) -> None:
    client.table("sessions").update(
        {"last_seen_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", session_id).execute()


def _rotate_session_token(
    client: Client,
    session_id: str,
    token: str,
    expires_at: datetime,
    user_agent: Optional[str],
    ip_address: Optional[str],
) -> None:
    client.table("sessions").update(
        {
            "token_hash": _token_hash(token),
            "user_agent": user_agent,
            "ip_address": ip_address,
            "expires_at": expires_at.isoformat(),
            "last_seen_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", session_id).execute()


def _revoke_session(client: Client, session_id: str) -> None:
    client.table("sessions").update(
        {"revoked_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", session_id).execute()


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token


async def get_current_auth_context(request: Request) -> dict:
    token = _extract_bearer_token(request)

    try:
        payload = jwt.decode(token, _get_jwt_secret_key(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        ) from None

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    client = get_supabase_client()
    session = await asyncio.to_thread(_fetch_active_session_by_token, client, token)
    if session is None or session.get("user_id") != user_id:
        raise HTTPException(status_code=401, detail="Session is invalid or expired")

    user = await asyncio.to_thread(_fetch_user_by_id, client, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")

    await asyncio.to_thread(_touch_session, client, session["id"])
    return {"client": client, "session": session, "token": token, "user": user}


# ════════════════════════════════════════════════════════════════════════
# データベースヘルパー関数
# ════════════════════════════════════════════════════════════════════════
# 注: これらはプライベート関数（先頭に _ を付けた慣例）で、APIエンドポイント内でのみ
#     使用されます。実際のデータベース操作はここに集約されているため、
#     修正時はこれらの関数だけを変更すれば済みます。


def _insert_conversation(client: Client, user_id: str | None = None) -> dict:
    """
    【新規会話を作成してデータベースに保存】
    空の会話レコードを conversations テーブルに挿入します。
    Supabase が自動的に id, created_at, updated_at を生成します。

    引数:
      client: Client
        → Supabase クライアントインスタンス

    戻り値:
      dict : 作成された会話レコード（id, title, created_at, updated_at を含む）

    例外:
      HTTPException(500) : データベース操作失敗時
    """
    if user_id is None:
        raise HTTPException(
            status_code=400, detail="ログイン情報を確認できませんでした"
        )

    try:
        result = client.table("conversations").insert({"user_id": user_id}).execute()
    except Exception as exc:
        logger.error("conversation insert failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="会話を作成できませんでした。時間をおいて再度お試しください。",
        ) from exc

    if not result.data:
        logger.error("conversation insert returned no data")
        raise HTTPException(
            status_code=503,
            detail="会話を作成できませんでした。時間をおいて再度お試しください。",
        )

    # 最初のレコード（実際には1件のみ）を返す
    return result.data[0]


def _fetch_conversations(client: Client, user_id: str | None = None) -> list[dict]:
    """Fetch recent conversations, optionally scoped to a user."""
    if user_id is None:
        raise HTTPException(
            status_code=400, detail="ログイン情報を確認できませんでした"
        )

    query = client.table("conversations").select("*")
    query = query.eq("user_id", user_id)

    try:
        result = query.order("updated_at", desc=True).limit(50).execute()
    except Exception as exc:
        logger.error("conversation fetch failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="会話履歴を読み込めませんでした。時間をおいて再度お試しください。",
        ) from exc
    return result.data or []


def _fetch_conversation(
    client: Client, conversation_id: str, user_id: str
) -> Optional[dict]:
    try:
        result = (
            client.table("conversations")
            .select("*")
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        logger.error("conversation lookup failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="会話を確認できませんでした。時間をおいて再度お試しください。",
        ) from exc
    return result.data[0] if result.data else None


def _fetch_messages(client: Client, conversation_id: str) -> list[dict]:
    """
    【指定会話に属するメッセージをすべて取得】
    messages テーブルから、指定会話IDのメッセージをすべて取得し、
    作成順（古い順）に並べて返します。

    引数:
      client: Client
        → Supabase クライアントインスタンス
      conversation_id: str
        → 検索対象の会話ID（UUID を文字列化したもの）

    戻り値:
      list[dict] : 該当するメッセージレコードのリスト。
                  作成日時の古い順に並んでいます。
    """
    try:
        result = (
            client.table("messages")
            .select("*")  # すべてのカラムを選択
            .eq("conversation_id", conversation_id)  # 指定会話IDで絞込
            .order("created_at")  # 作成日時で古い順にソート
            .execute()
        )
    except Exception as exc:
        logger.error("message fetch failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="メッセージ履歴を読み込めませんでした。時間をおいて再度お試しください。",
        ) from exc
    return result.data or []


def _insert_message(
    client: Client, conversation_id: str, role: str, content: str
) -> dict:
    """
    【メッセージを新規作成してデータベースに保存】
    messages テーブルに新しいメッセージレコードを挿入します。

    引数:
      client: Client
        → Supabase クライアントインスタンス
      conversation_id: str
        → このメッセージが属する会話ID（UUID を文字列化したもの）
      role: str
        → メッセージの送信者種別。"user" または "bot"。
      content: str
        → メッセージの本文テキスト

    戻り値:
      dict : 作成されたメッセージレコード（すべてのカラムを含む）

    例外:
      HTTPException(500) : データベース操作失敗時
    """
    try:
        result = (
            client.table("messages")
            .insert(
                {"conversation_id": conversation_id, "role": role, "content": content}
            )
            .execute()
        )
    except Exception as exc:
        logger.error("message insert failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="メッセージを保存できませんでした。時間をおいて再度お試しください。",
        ) from exc
    if not result.data:
        logger.error("message insert returned no data")
        raise HTTPException(
            status_code=503,
            detail="メッセージを保存できませんでした。時間をおいて再度お試しください。",
        )
    return result.data[0]


def _touch_conversation(client: Client, conversation_id: str) -> None:
    """
    【会話の更新日時を現在時刻に更新】
    メッセージが新規追加されたときに呼び出され、
    その会話を「最近更新」として一覧の先頭にソート直すために使用されます。

    引数:
      client: Client
        → Supabase クライアントインスタンス
      conversation_id: str
        → 更新対象の会話ID（UUID を文字列化したもの）

    戻り値:
      None（戻り値なし）
    """
    try:
        client.table("conversations").update({"updated_at": "now()"}).eq(
            "id", conversation_id
        ).execute()
    except Exception as exc:
        logger.error("conversation touch failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="会話の更新に失敗しました。時間をおいて再度お試しください。",
        ) from exc


# ════════════════════════════════════════════════════════════════════════
# スキル管理 DB ヘルパー関数
# ════════════════════════════════════════════════════════════════════════


def _fetch_skills(client: Client) -> list[dict]:
    """
    【登録済みスキル一覧を取得】
    skills テーブルから全レコードを作成日時の新しい順で返す。

    引数:
      client: Client → Supabase クライアントインスタンス

    戻り値:
      list[dict] : スキルレコードのリスト
    """
    result = client.table("skills").select("*").order("created_at", desc=True).execute()
    return result.data


def _insert_skill(client: Client, data: dict) -> dict:
    """
    【スキルを新規作成してDBに保存】
    skills テーブルに1件挿入し、作成されたレコードを返す。

    引数:
      client: Client → Supabase クライアントインスタンス
      data: dict     → 挿入するスキルデータ（name, description, action_url 等）

    戻り値:
      dict : 作成されたスキルレコード

    例外:
      HTTPException(500) : DB への挿入が失敗した場合
    """
    result = client.table("skills").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="スキルの作成に失敗しました")
    return result.data[0]


def _delete_skill(client: Client, skill_id: str) -> None:
    """
    【スキルをDBから削除】
    skills テーブルから指定 ID のレコードを削除する。

    引数:
      client: Client  → Supabase クライアントインスタンス
      skill_id: str   → 削除対象のスキル UUID（文字列形式）

    戻り値:
      None（戻り値なし）
    """
    client.table("skills").delete().eq("id", skill_id).execute()


def _extract_json_object(text: str) -> Optional[dict]:
    """文字列中から JSON オブジェクトを抽出して返す。"""
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        loaded = json.loads(text[start : end + 1])
        if isinstance(loaded, dict):
            return loaded
    except json.JSONDecodeError:
        return None
    return None


def _build_skill_draft_from_text(message: str) -> Optional[dict]:
    """フォールバック用: メッセージから簡易スキル下書きを生成する。"""
    normalized = message.strip()
    if not normalized:
        return None
    return {
        "name": "new_skill",
        "description": f"ユーザー依頼: {normalized[:120]}",
        "action_url": "https://example.com/webhook",
        "action_method": "POST",
        "action_body_template": '{"input":"{input}"}',
    }


def _build_chat_prompt(history_rows: list[dict], user_message: str) -> str:
    """Gemini に渡すチャット履歴プロンプトを組み立てる。"""
    recent_rows = history_rows[-MAX_CHAT_CONTEXT_MESSAGES:]
    lines = [
        f"System: {CHAT_SYSTEM_PROMPT}",
        "",
        "Conversation history:",
    ]
    for row in recent_rows:
        role = "Assistant" if row.get("role") == "bot" else "User"
        content = row.get("content")
        if content:
            lines.append(f"{role}: {content}")
    lines.extend(["", f"User: {user_message}", "Assistant:"])
    return "\n".join(lines)


def _month_to_date(target_month: str) -> str:
    """HTML month input の YYYY-MM をDB用の月初日へ変換する。"""
    return f"{target_month}-01"


def _task_create_payload(req: AutomationTaskCreate) -> dict:
    """フロントのタスク設定をDBスキーマに合わせる。"""
    return {
        "name": req.task_name,
        "description": "月次成果物生成タスク",
        "template_path": req.template_path,
        "output_directory": req.output_directory,
        "filename_policy": {
            "mode": req.output_filename_policy,
            "confirm_when_unknown": req.output_filename_policy == "confirm_each_time",
        },
        "approval_policy": {
            "login_before_after": req.require_login_confirmation,
            "regeneration_requires_explicit_approval": (
                req.require_regeneration_approval
            ),
        },
        "blocked_site_rules": [
            {"site_name": site} for site in req.blocked_sites if site.strip()
        ],
    }


def _http_error_from_exception(
    exc: Exception, fallback_status: int = 500
) -> HTTPException:
    """サービス層の例外をAPI向けに変換する。"""
    return HTTPException(status_code=fallback_status, detail=str(exc))


def _credential_public(row: dict) -> dict:
    """暗号文そのものをAPIレスポンスから落とす。"""
    public_row = dict(row)
    public_row.pop("encrypted_secret", None)
    public_row.pop("encryption_nonce", None)
    return public_row


# ════════════════════════════════════════════════════════════════════════
# REST API エンドポイント
# ════════════════════════════════════════════════════════════════════════
# 注: 各エンドポイントは async 定義されており、非同期処理に対応しています。
#     asyncio.to_thread() でスレッド内でブロッキング処理を実行することで
#     他のリクエスト処理をブロックしません。


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request) -> LoginResponse:
    client = get_supabase_client()
    user = await asyncio.to_thread(_fetch_user_by_email, client, req.email)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    password_ok = await asyncio.to_thread(
        _verify_password, req.password, user["password_hash"]
    )
    if not password_ok:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token, expires_at = _create_access_token(user["id"])
    await asyncio.to_thread(
        _insert_session,
        client,
        user["id"],
        token,
        expires_at,
        request.headers.get("user-agent"),
        _request_ip_address(request),
    )

    public_user = {k: v for k, v in user.items() if k != "password_hash"}
    return LoginResponse(
        token=token,
        access_token=token,
        expires_at=expires_at.isoformat(),
        user=AuthUserResponse(**public_user),
    )


@app.post("/api/auth/signup", response_model=LoginResponse, status_code=201)
async def signup(req: LoginRequest, request: Request) -> LoginResponse:
    logger.info("signup request started: email=%s", req.email)
    try:
        logger.info("getting Supabase client")
        client = get_supabase_client()
        logger.info("checking if email already exists")
        existing_user = await asyncio.to_thread(_fetch_user_by_email, client, req.email)
        if existing_user is not None:
            logger.info("email already registered: %s", req.email)
            raise HTTPException(status_code=409, detail="Email is already registered")

        logger.info("hashing password")
        password_hash = await asyncio.to_thread(_hash_password, req.password)
        try:
            logger.info("inserting user into database")
            user = await asyncio.to_thread(_insert_user, client, req.email, password_hash)
        except HTTPException:
            logger.error("HTTP exception during user insert")
            raise
        except APIError as exc:
            if _is_unique_constraint_violation(exc):
                logger.info("unique constraint violation detected: %s", req.email)
                raise HTTPException(
                    status_code=409, detail="Email is already registered"
                ) from None
            logger.error("APIError during signup: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create user") from exc
        except ValueError as exc:
            logger.error("ValueError during signup: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create user") from exc
        except Exception as exc:
            logger.error("Unexpected exception during signup: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create user") from exc

        logger.info("generating access token")
        token, expires_at = _create_access_token(user["id"])
        logger.info("access token generated successfully")
        logger.info("inserting session")
        await asyncio.to_thread(
            _insert_session,
            client,
            user["id"],
            token,
            expires_at,
            request.headers.get("user-agent"),
            _request_ip_address(request),
        )
        logger.info("session inserted successfully")

        logger.info("signup completed successfully: email=%s", req.email)
        public_user = {k: v for k, v in user.items() if k != "password_hash"}
        return LoginResponse(
            token=token,
            access_token=token,
            expires_at=expires_at.isoformat(),
            user=AuthUserResponse(**public_user),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("unexpected error in signup: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create user") from exc


@app.get("/api/auth/me", response_model=AuthUserResponse)
async def get_current_user(
    auth_context: dict = Depends(get_current_auth_context),
) -> AuthUserResponse:
    return AuthUserResponse(**auth_context["user"])


@app.post("/api/auth/refresh", response_model=LoginResponse)
async def refresh_token(
    request: Request,
    auth_context: dict = Depends(get_current_auth_context),
) -> LoginResponse:
    user = auth_context["user"]
    session = auth_context["session"]
    client = auth_context["client"]

    token, expires_at = _create_access_token(user["id"])
    await asyncio.to_thread(
        _rotate_session_token,
        client,
        session["id"],
        token,
        expires_at,
        request.headers.get("user-agent"),
        _request_ip_address(request),
    )

    return LoginResponse(
        token=token,
        access_token=token,
        expires_at=expires_at.isoformat(),
        user=AuthUserResponse(**user),
    )


@app.post("/api/auth/logout", response_model=LogoutResponse)
async def logout(
    auth_context: dict = Depends(get_current_auth_context),
) -> LogoutResponse:
    await asyncio.to_thread(
        _revoke_session,
        auth_context["client"],
        auth_context["session"]["id"],
    )
    return LogoutResponse(success=True)


@app.post("/api/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    current_user: dict = Depends(get_current_auth_context),
) -> ConversationResponse:
    client = current_user["client"]
    user_id = current_user["user"]["id"]
    row = await asyncio.to_thread(_insert_conversation, client, user_id)
    return ConversationResponse(**row)


@app.get("/api/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: dict = Depends(get_current_auth_context),
) -> list[ConversationResponse]:
    client = current_user["client"]
    user_id = current_user["user"]["id"]
    rows = await asyncio.to_thread(_fetch_conversations, client, user_id)
    return [ConversationResponse(**row) for row in rows]


@app.get(
    "/api/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
async def list_messages(
    conversation_id: uuid.UUID,
    current_user: dict = Depends(get_current_auth_context),
) -> list[MessageResponse]:
    client = current_user["client"]
    user_id = current_user["user"]["id"]
    conversation = await asyncio.to_thread(
        _fetch_conversation,
        client,
        str(conversation_id),
        user_id,
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    rows = await asyncio.to_thread(_fetch_messages, client, str(conversation_id))
    return [MessageResponse(**row) for row in rows]


@app.post("/api/chat")
async def chat(
    req: ChatRequest,
    current_user: dict = Depends(get_current_auth_context),
) -> StreamingResponse:
    try:
        gemini_client = create_gemini_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    client = current_user["client"]
    user_id = current_user["user"]["id"]

    if req.conversation_id is None:
        conv_row = await asyncio.to_thread(_insert_conversation, client, user_id)
        conv_id: str = conv_row["id"]
    else:
        conv_id = str(req.conversation_id)
        conversation = await asyncio.to_thread(
            _fetch_conversation,
            client,
            conv_id,
            user_id,
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

    history_rows = await asyncio.to_thread(_fetch_messages, client, conv_id)
    prompt = _build_chat_prompt(history_rows, req.message)

    async def event_stream():
        final_reply = ""
        try:
            async for delta in stream_gemini_text(
                gemini_client,
                prompt,
                temperature=0.7,
            ):
                final_reply += delta
                payload = json.dumps({"chunk": delta}, ensure_ascii=False)
                yield f"data: {payload}\n\n"

            await asyncio.to_thread(
                _insert_message, client, conv_id, "user", req.message
            )
            if final_reply:
                await asyncio.to_thread(
                    _insert_message, client, conv_id, "bot", final_reply
                )
            await asyncio.to_thread(_touch_conversation, client, conv_id)
        except Exception as exc:
            logger.error("chat streaming error: %s", exc, exc_info=True)
            payload = json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"data: {payload}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/automation/sites", response_model=list[AutomationSiteResponse])
async def list_automation_sites() -> list[AutomationSiteResponse]:
    """自動化対象サイトの一覧を取得する。"""
    client = get_supabase_client()
    try:
        rows = await asyncio.to_thread(automation_service.list_sites, client)
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    return [AutomationSiteResponse(**row) for row in rows]


@app.post(
    "/api/automation/sites",
    response_model=AutomationSiteResponse,
    status_code=201,
)
async def create_automation_site(
    req: AutomationSiteCreate,
) -> AutomationSiteResponse:
    """自動化対象サイトを登録する。"""
    client = get_supabase_client()
    try:
        row = await asyncio.to_thread(
            automation_service.create_site,
            client,
            {
                "name": req.name,
                "category": req.category,
                "base_url": req.base_url,
                "allowed_domains": req.allowed_domains,
                "blocked_site_rules": req.blocked_site_rules,
            },
        )
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    return AutomationSiteResponse(**row)


@app.get(
    "/api/automation/credentials",
    response_model=list[SiteCredentialResponse],
)
async def list_site_credentials(
    site_id: Optional[str] = None,
) -> list[SiteCredentialResponse]:
    """登録済みサイト認証情報を、秘密情報を除いて取得する。"""
    client = get_supabase_client()
    filters = {"site_id": site_id} if site_id else None
    try:
        rows = await asyncio.to_thread(
            automation_service.list_credentials, client, filters
        )
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    return [SiteCredentialResponse(**_credential_public(row)) for row in rows]


@app.post(
    "/api/automation/credentials",
    response_model=SiteCredentialResponse,
    status_code=201,
)
async def create_site_credential(
    req: SiteCredentialCreate,
) -> SiteCredentialResponse:
    """サイト認証情報を暗号化して保存する。"""
    client = get_supabase_client()
    try:
        row = await asyncio.to_thread(
            automation_service.create_credential,
            client,
            {
                "site_id": req.site_id,
                "account_identifier": req.account_identifier,
                "metadata_json": req.metadata_json,
            },
            req.secret,
        )
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    return SiteCredentialResponse(**_credential_public(row))


@app.get("/api/automation/tasks", response_model=list[AutomationTaskResponse])
async def list_automation_tasks() -> list[AutomationTaskResponse]:
    """業務自動化タスク設定の一覧を取得する。"""
    client = get_supabase_client()
    try:
        rows = await asyncio.to_thread(automation_service.list_tasks, client)
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    return [AutomationTaskResponse(**row) for row in rows]


@app.post(
    "/api/automation/tasks",
    response_model=AutomationTaskResponse,
    status_code=201,
)
async def create_automation_task(
    req: AutomationTaskCreate,
) -> AutomationTaskResponse:
    """業務自動化タスク設定を保存する。"""
    client = get_supabase_client()
    payload = _task_create_payload(req)
    try:
        row = await asyncio.to_thread(automation_service.create_task, client, payload)
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    return AutomationTaskResponse(**row)


@app.get(
    "/api/automation/tasks/{task_id}",
    response_model=AutomationTaskResponse,
)
async def get_automation_task(task_id: str) -> AutomationTaskResponse:
    """業務自動化タスク設定を1件取得する。"""
    client = get_supabase_client()
    try:
        row = await asyncio.to_thread(automation_service.get_task, client, task_id)
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    if not row:
        raise HTTPException(status_code=404, detail="自動化タスクが見つかりません")
    return AutomationTaskResponse(**row)


@app.delete("/api/automation/tasks/{task_id}", status_code=204)
async def delete_automation_task(task_id: str) -> None:
    """業務自動化タスク設定を削除する。"""
    client = get_supabase_client()
    try:
        await asyncio.to_thread(automation_service.delete_task, client, task_id)
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc


@app.get("/api/automation/runs", response_model=list[AutomationRunResponse])
async def list_automation_runs(
    task_id: Optional[str] = None,
) -> list[AutomationRunResponse]:
    """業務自動化タスクの実行履歴を取得する。"""
    client = get_supabase_client()
    filters = {"task_id": task_id} if task_id else None
    try:
        rows = await asyncio.to_thread(automation_service.list_runs, client, filters)
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    return [AutomationRunResponse(**row) for row in rows]


@app.post(
    "/api/automation/runs",
    response_model=AutomationRunResponse,
    status_code=201,
)
async def create_automation_run(req: AutomationRunCreate) -> AutomationRunResponse:
    """業務自動化タスクの実行履歴を開始状態で作成する。"""
    client = get_supabase_client()
    target_month = _month_to_date(req.target_month)
    try:
        existing = await asyncio.to_thread(
            automation_service.find_generated_file_for_month,
            client,
            req.task_id,
            target_month,
        )
        if (
            existing
            and req.require_regeneration_approval
            and not req.approved_regeneration
        ):
            raise HTTPException(
                status_code=409,
                detail="同月の生成済みファイルがあります。再生成には明示承認が必要です。",
            )
        row = await asyncio.to_thread(
            automation_service.create_run,
            client,
            {
                "task_id": req.task_id,
                "skill_id": req.skill_id,
                "target_month": target_month,
                "status": "queued",
                "resume_state_json": {
                    "reason": "created_from_api",
                    "stop_position": None,
                },
            },
        )
        await asyncio.to_thread(
            automation_service.append_run_log,
            client,
            row["id"],
            "info",
            "実行履歴を作成しました。ブラウザ自動操作の実装後にこの位置から開始します。",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    return AutomationRunResponse(**row)


@app.get(
    "/api/automation/runs/{run_id}/logs",
    response_model=list[AutomationLogResponse],
)
async def list_automation_run_logs(run_id: str) -> list[AutomationLogResponse]:
    """指定実行のログを取得する。チャット画面表示にも使う。"""
    client = get_supabase_client()
    try:
        rows = await asyncio.to_thread(
            automation_service.list_logs, client, {"run_id": run_id}
        )
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    return [AutomationLogResponse(**row) for row in rows]


@app.post(
    "/api/automation/logs",
    response_model=AutomationLogResponse,
    status_code=201,
)
async def create_automation_log(req: AutomationLogCreate) -> AutomationLogResponse:
    """業務自動化実行ログを追加する。"""
    client = get_supabase_client()
    try:
        row = await asyncio.to_thread(
            automation_service.create_log,
            client,
            {
                "run_id": req.run_id,
                "level": req.level,
                "message": req.message,
                "user_action_message": req.user_action_message,
                "details_json": req.details_json,
            },
        )
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    return AutomationLogResponse(**row)


@app.get(
    "/api/automation/generated-files",
    response_model=list[GeneratedFileResponse],
)
async def list_generated_files(
    task_id: Optional[str] = None,
    target_month: Optional[str] = None,
) -> list[GeneratedFileResponse]:
    """生成済みファイルを取得する。同月再生成の警告判定にも使う。"""
    client = get_supabase_client()
    filters = {"task_id": task_id} if task_id else {}
    if target_month:
        filters["target_month"] = _month_to_date(target_month)
    try:
        rows = await asyncio.to_thread(
            automation_service.list_generated_files,
            client,
            filters or None,
        )
    except Exception as exc:
        raise _http_error_from_exception(exc) from exc
    return [GeneratedFileResponse(**row) for row in rows]


@app.get("/api/skills", response_model=list[SkillResponse])
async def list_skills() -> list[SkillResponse]:
    """
    【GET /api/skills】 登録済みスキル一覧を取得するエンドポイント

    【役割】
    エージェントUIや管理画面でスキル一覧を表示する際に使用する。
    登録日時の新しい順で全件返却する。

    【レスポンス】
    list[SkillResponse]（HTTP 200 OK）

    【例】
    curl http://localhost:8000/api/skills
    → [{"id": "...", "name": "my_skill", ...}, ...]
    """
    client = get_supabase_client()
    rows = await asyncio.to_thread(_fetch_skills, client)
    return [SkillResponse(**r) for r in rows]


@app.post("/api/skills", response_model=SkillResponse, status_code=201)
async def create_skill(req: SkillCreate) -> SkillResponse:
    """
    【POST /api/skills】 新規スキルを登録するエンドポイント

    【役割】
    カスタム Webhook をスキルとして登録し、エージェントから呼び出し可能にする。

    【リクエストボディ】
    SkillCreate
    - name: スキルの識別名（必須）
    - description: スキルの説明（必須）
    - action_url: Webhook URL（必須）
    - action_method: HTTP メソッド（省略時 "POST"）
    - action_body_template: ボディテンプレート（省略時 ""）

    【レスポンス】
    SkillResponse（HTTP 201 Created）

    【例】
    curl -X POST http://localhost:8000/api/skills \\
      -H "Content-Type: application/json" \\
      -d '{"name": "my_skill", "description": "...", "action_url": "https://..."}'
    → {"id": "...", "name": "my_skill", ...}
    """
    client = get_supabase_client()
    data = {
        "name": req.name,
        "description": req.description,
        "action_url": req.action_url,
        "action_method": req.action_method,
        "action_body_template": req.action_body_template,
    }
    row = await asyncio.to_thread(_insert_skill, client, data)
    return SkillResponse(**row)


@app.delete("/api/skills/{skill_id}", status_code=204)
async def delete_skill(skill_id: str) -> None:
    """
    【DELETE /api/skills/{skill_id}】 スキルを削除するエンドポイント

    【役割】
    登録済みスキルを ID 指定で削除する。

    【パスパラメータ】
    skill_id : 削除対象のスキル UUID（文字列形式）

    【レスポンス】
    HTTP 204 No Content（ボディなし）

    【例】
    curl -X DELETE http://localhost:8000/api/skills/550e8400-e29b-41d4-a716-446655440000
    → (204 No Content)
    """
    client = get_supabase_client()
    await asyncio.to_thread(_delete_skill, client, skill_id)


@app.post("/api/skills/assistant", response_model=SkillAssistantResponse)
async def skill_assistant(req: SkillAssistantRequest) -> SkillAssistantResponse:
    """
    【POST /api/skills/assistant】AI と対話してスキル下書きを作る。

    入力メッセージから、登録フォームにそのまま反映できる draft を返す。
    """
    prompt = f"""
あなたは業務自動化スキル設計アシスタントです。
ユーザーの要望から webhook スキル案を作成してください。

必ず次の JSON だけを返答してください:
{{
  "reply": "ユーザーへの日本語メッセージ",
  "draft": {{
    "name": "snake_case_name",
    "description": "いつ使うスキルか",
    "action_url": "https://...",
    "action_method": "GET or POST",
    "action_body_template": "{{\\"input\\":\\"{{input}}\\"}}"
  }}
}}

ルール:
- URL が不明な場合は draft.action_url を "https://example.com/webhook" にする
- ユーザー情報が不足していても、必ず暫定 draft を返す
- draft.name は英数字とアンダースコアのみ

会話履歴:
{json.dumps(req.history, ensure_ascii=False)}

最新のユーザー入力:
{req.message}
""".strip()

    assistant_reply = (
        "暫定のスキル案を作成しました。内容を確認して必要なら修正してください。"
    )
    draft_data = _build_skill_draft_from_text(req.message)

    try:
        gemini_client = create_gemini_client()
        content = await generate_gemini_text(
            gemini_client,
            prompt,
            temperature=0.2,
            max_output_tokens=1024,
        )
        parsed = _extract_json_object(content)
        if parsed:
            assistant_reply = parsed.get("reply") or assistant_reply
            if isinstance(parsed.get("draft"), dict):
                draft_data = parsed["draft"]
    except Exception as exc:
        logger.warning("skills assistant fallback: %s", exc)

    if not draft_data:
        raise HTTPException(status_code=400, detail="メッセージが空です")

    try:
        draft = SkillCreate(**draft_data)
    except Exception as exc:
        logger.warning("skills assistant invalid draft: %s", exc)
        safe_draft = _build_skill_draft_from_text(req.message)
        draft = SkillCreate(**safe_draft)
        assistant_reply = (
            "入力情報が不足していたため、暫定テンプレートで作成しました。"
            " URLや説明を調整してから登録してください。"
        )

    return SkillAssistantResponse(reply=assistant_reply, draft=draft)


@app.post("/api/agent/chat")
async def agent_chat(
    req: ChatRequest,
    current_user: dict = Depends(get_current_auth_context),
) -> StreamingResponse:
    """
    POST /api/agent/chat
    ReAct エージェントを起動し、思考ステップを SSE でストリーミング返却する。
    ユーザーメッセージと最終回答は messages テーブルに保存される。
    各思考ステップは agent_steps テーブルに記録される。
    """
    try:
        gemini_client = create_gemini_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    supabase = current_user["client"]
    user_id = current_user["user"]["id"]

    if req.conversation_id is None:
        conv_row = await asyncio.to_thread(_insert_conversation, supabase, user_id)
        conv_id: str = conv_row["id"]
    else:
        conv_id = str(req.conversation_id)
        conversation = await asyncio.to_thread(
            _fetch_conversation,
            supabase,
            conv_id,
            user_id,
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

    user_msg_row = await asyncio.to_thread(
        _insert_message, supabase, conv_id, "user", req.message
    )
    message_id: str = user_msg_row["id"]
    skills = await asyncio.to_thread(_fetch_skills, supabase)

    async def event_stream():
        final_reply = ""
        try:
            async for step in run_agent(
                req.message, gemini_client, supabase, message_id, skills
            ):
                yield build_agent_event(step, conv_id)
                if step.step_type == "answer":
                    final_reply = step.content
        except Exception as exc:
            logger.error("エージェントエラー: %s", exc, exc_info=True)
            error_payload = json.dumps(
                {"type": "error", "content": str(exc)}, ensure_ascii=False
            )
            yield f"data: {error_payload}\n\n"

        if final_reply:
            await asyncio.to_thread(
                _insert_message, supabase, conv_id, "bot", final_reply
            )
            await asyncio.to_thread(_touch_conversation, supabase, conv_id)

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# タスク実行 API ルーター統合
try:
    from api.task_api import router as task_router

    app.include_router(task_router)
except ImportError:
    logger.warning("task_api モジュールのインポートに失敗しました")

# Vercel では静的ファイルは CDN が配信するため、ローカル開発時のみマウントする。
# VERCEL 環境変数が設定されている場合（Vercel 関数実行環境）はスキップする。
_static_dir = os.path.join(os.path.dirname(__file__), "..", "public")
if not os.environ.get("VERCEL") and os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
