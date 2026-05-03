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
import json
import logging
import os
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import Client, create_client

from api.agent_service import build_agent_event, run_agent

logger = logging.getLogger(__name__)

# FastAPI アプリケーションインスタンスを作成
app = FastAPI()

# ────────────────────────────────────────────────────────────────────────
# CORS（Cross-Origin Resource Sharing）設定
# ────────────────────────────────────────────────────────────────────────
# 目的: フロントエンドから異なるオリジン（ドメイン）からのリクエストを許可
# 設定内容:
#   - allow_origins=["*"] : すべてのオリジンからのリクエストを許可
#   - allow_methods=["*"] : すべてのHTTPメソッド(GET,POST,PUT等)を許可
#   - allow_headers=["*"] : すべてのリクエストヘッダーを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────────────────────────────────────
# 静的ファイルのマウント（HTML/JS/CSS を提供）
# ────────────────────────────────────────────────────────────────────────
# 目的: フロントエンド資産（HTML,JavaScript,CSS）をクライアントに配信
# 設定内容:
#   - "/" : ルートパスに マウント
#   - directory: ../public フォルダを静的資源フォルダとして指定
#   - html=True : index.html への自動フォールバックを有効化
#                 （存在しないパスへのアクセスは index.html を返す）
app.mount(
    "/",
    StaticFiles(
        directory=os.path.join(os.path.dirname(__file__), "..", "public"), html=True
    ),
    name="static",
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
    # 環境変数から Supabase の URL と API キーを取得
    url: str = os.environ["SUPABASE_URL"]
    key: str = os.environ["SUPABASE_ANON_KEY"]

    # 取得した認証情報でクライアントを生成・返却
    return create_client(url, key)


# ════════════════════════════════════════════════════════════════════════
# データベースヘルパー関数
# ════════════════════════════════════════════════════════════════════════
# 注: これらはプライベート関数（先頭に _ を付けた慣例）で、APIエンドポイント内でのみ
#     使用されます。実際のデータベース操作はここに集約されているため、
#     修正時はこれらの関数だけを変更すれば済みます。


def _insert_conversation(client: Client) -> dict:
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
    # 空オブジェクト {} を挿入（Supabase が自動フィールドを生成）
    result = client.table("conversations").insert({}).execute()

    # 結果チェック：データが取得できなかった場合はエラー
    if not result.data:
        raise HTTPException(status_code=500, detail="会話の作成に失敗しました")

    # 最初のレコード（実際には1件のみ）を返す
    return result.data[0]


def _fetch_conversations(client: Client) -> list[dict]:
    """
    【すべての会話一覧を取得】
    conversations テーブルから最新50件の会話を、
    更新日時の新しい順に取得します。

    引数:
      client: Client
        → Supabase クライアントインスタンス

    戻り値:
      list[dict] : 会話レコードのリスト（最大50件）。
                  更新日時の新しい順に並んでいます。
    """
    result = (
        client.table("conversations")
        .select("*")  # すべてのカラムを選択
        .order("updated_at", desc=True)  # 更新日時で新しい順にソート
        .limit(50)  # 最大50件に制限
        .execute()
    )
    return result.data


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
    result = (
        client.table("messages")
        .select("*")  # すべてのカラムを選択
        .eq("conversation_id", conversation_id)  # 指定会話IDで絞込
        .order("created_at")  # 作成日時で古い順にソート
        .execute()
    )
    return result.data


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
    result = (
        client.table("messages")
        .insert({"conversation_id": conversation_id, "role": role, "content": content})
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="メッセージの保存に失敗しました")
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
    # 指定会話の updated_at を現在時刻（now()）に更新
    client.table("conversations").update({"updated_at": "now()"}).eq(
        "id", conversation_id
    ).execute()


# ════════════════════════════════════════════════════════════════════════
# REST API エンドポイント
# ════════════════════════════════════════════════════════════════════════
# 注: 各エンドポイントは async 定義されており、非同期処理に対応しています。
#     asyncio.to_thread() でスレッド内でブロッキング処理を実行することで
#     他のリクエスト処理をブロックしません。


@app.post("/api/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation() -> ConversationResponse:
    """
    【POST /api/conversations】 新規会話を作成するエンドポイント

    【役割】
    クライアントが新しいチャット会話を開始する際に呼び出されます。
    ユーザーが「新しいチャット」をクリックしたときに実行されます。

    【リクエスト】
    クエリパラメータ・ボディなし

    【レスポンス】
    ConversationResponse（HTTP 201 Created）
    - id: 新規に生成された会話ID
    - title: 空文字列（最初のメッセージで自動設定）
    - created_at: 作成日時
    - updated_at: 作成日時と同じ

    【例】
    curl -X POST http://localhost:8000/api/conversations
    → {"id": "...", "title": "", "created_at": "...", "updated_at": "..."}
    """
    client = get_supabase_client()
    row = await asyncio.to_thread(_insert_conversation, client)
    return ConversationResponse(**row)


@app.get("/api/conversations", response_model=list[ConversationResponse])
async def list_conversations() -> list[ConversationResponse]:
    """
    【GET /api/conversations】 会話一覧を取得するエンドポイント

    【役割】
    サイドバーの「最近のチャット」欄に表示する会話一覧を取得します。
    ページ読込時と「新しいチャット」作成後に呼び出されます。

    【リクエスト】
    クエリパラメータなし

    【レスポンス】
    list[ConversationResponse]
    - 最大50件の会話を、更新日時の新しい順に返す
    - 最近やり取りがあった会話が先頭に来る

    【例】
    curl http://localhost:8000/api/conversations
    → [{"id": "...", "title": "...", ...}, ...]
    """
    client = get_supabase_client()
    rows = await asyncio.to_thread(_fetch_conversations, client)
    return [ConversationResponse(**r) for r in rows]


@app.get(
    "/api/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
async def list_messages(conversation_id: uuid.UUID) -> list[MessageResponse]:
    """
    【GET /api/conversations/{conversation_id}/messages】
    指定会話のメッセージ一覧を取得するエンドポイント

    【役割】
    サイドバーの過去会話をクリックしたとき、その会話の過去メッセージを
    チャット画面に読み込みます。

    【パスパラメータ】
    conversation_id : 照会対象の会話ID（UUID 形式）

    【レスポンス】
    list[MessageResponse]
    - 指定会話に属するすべてのメッセージを、作成日時の古い順に返す
    - ユーザーメッセージと AI メッセージが時系列で混在

    【例】
    curl http://localhost:8000/api/conversations/550e8400-e29b-41d4-a716-446655440000/messages
    → [{"id": "...", "role": "user", "content": "...", ...}, ...]
    """
    client = get_supabase_client()
    rows = await asyncio.to_thread(_fetch_messages, client, str(conversation_id))
    return [MessageResponse(**r) for r in rows]


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    【POST /api/chat】 チャットメッセージを送信して AI 応答を取得するエンドポイント

    【役割】
    チャットUIからユーザーメッセージを受け取り、
    それをデータベースに保存し、AI応答を生成・保存して返却します。
    このエンドポイントが最も頻繁に使用されるメインのチャット機能です。

    【リクエストボディ】
    ChatRequest
    - message: 必須。ユーザーの入力テキスト
    - conversation_id: 任意。既存会話の場合は指定、新規会話の場合は null

    【処理フロー】
    1. conversation_id が null なら新規会話を作成
    2. ユーザーメッセージを messages テーブルに保存（role="user"）
    3. AI応答を生成（実装例では単純な返信文）
    4. AI応答を messages テーブルに保存（role="bot"）
    5. 会話の updated_at を更新（一覧ソート用）
    6. AI応答と会話IDをクライアントに返す

    【レスポンス】
    ChatResponse（HTTP 200 OK）
    - reply: AI が生成した応答テキスト
    - conversation_id: メッセージが属する会話ID
      （新規会話の場合、ここで初めて会話IDが通知される）

    【例】
    curl -X POST http://localhost:8000/api/chat \
      -H "Content-Type: application/json" \
      -d '{"message": "Hello!", "conversation_id": null}'
    → {"reply": "Pythonからの返信: Hello!", "conversation_id": "..."}
    """
    # Supabase クライアントを取得
    client = get_supabase_client()

    # 新規会話か既存会話かで処理を分岐
    if req.conversation_id is None:
        # 新規会話：conversations テーブルに新しい行を作成
        conv_row = await asyncio.to_thread(_insert_conversation, client)
        conv_id: str = conv_row["id"]
    else:
        # 既存会話：指定された ID を使用
        conv_id = str(req.conversation_id)

    # ユーザーのメッセージを messages テーブルに保存
    # role="user" で「ユーザーが送信した」と記録
    await asyncio.to_thread(_insert_message, client, conv_id, "user", req.message)

    # AI応答を生成
    # （現在の実装は単純な返信。将来的に OpenAI API 等と統合）
    reply: str = f"Pythonからの返信: {req.message}"

    # AI応答を messages テーブルに保存
    # role="bot" で「AIが生成した」と記録
    await asyncio.to_thread(_insert_message, client, conv_id, "bot", reply)

    # 会話の updated_at を現在時刻に更新
    # （サイドバーの一覧で新しい順にソートされるため）
    await asyncio.to_thread(_touch_conversation, client, conv_id)

    # クライアントに応答を返す
    return ChatResponse(reply=reply, conversation_id=uuid.UUID(conv_id))


@app.post("/api/agent/chat")
async def agent_chat(req: ChatRequest) -> StreamingResponse:
    """
    POST /api/agent/chat
    ReAct エージェントを起動し、思考ステップを SSE でストリーミング返却する。
    ユーザーメッセージと最終回答は messages テーブルに保存される。
    各思考ステップは agent_steps テーブルに記録される。
    """
    try:
        from groq import AsyncGroq
    except ImportError as exc:
        raise HTTPException(
            status_code=503, detail="groq パッケージが未インストールです"
        ) from exc

    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY が設定されていません")

    groq_client = AsyncGroq(api_key=groq_key)
    supabase = get_supabase_client()

    if req.conversation_id is None:
        conv_row = await asyncio.to_thread(_insert_conversation, supabase)
        conv_id: str = conv_row["id"]
    else:
        conv_id = str(req.conversation_id)

    user_msg_row = await asyncio.to_thread(
        _insert_message, supabase, conv_id, "user", req.message
    )
    message_id: str = user_msg_row["id"]

    async def event_stream():
        final_reply = ""
        try:
            async for step in run_agent(req.message, groq_client, supabase, message_id):
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
