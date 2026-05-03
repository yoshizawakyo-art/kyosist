import asyncio
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import Client, create_client

# src/ を sys.path に追加して agent_service を参照できるようにする
_SRC_ROOT = Path(__file__).resolve().parent / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from api.agent_service import build_agent_event, run_agent  # noqa: E402

logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models ──────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[uuid.UUID] = None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    created_at: str


class ChatResponse(BaseModel):
    reply: str
    conversation_id: uuid.UUID


# ── Supabase client ──────────────────────────────────────────


def get_supabase_client() -> Client:
    url: str = os.environ["SUPABASE_URL"]
    key: str = os.environ["SUPABASE_ANON_KEY"]
    return create_client(url, key)


# ── DB helpers ───────────────────────────────────────────────


def _insert_conversation(client: Client) -> dict:
    result = client.table("conversations").insert({}).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="会話の作成に失敗しました")
    return result.data[0]


def _fetch_conversations(client: Client) -> list[dict]:
    result = (
        client.table("conversations")
        .select("*")
        .order("updated_at", desc=True)
        .limit(50)
        .execute()
    )
    return result.data


def _fetch_messages(client: Client, conversation_id: str) -> list[dict]:
    result = (
        client.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )
    return result.data


def _insert_message(
    client: Client, conversation_id: str, role: str, content: str
) -> dict:
    result = (
        client.table("messages")
        .insert({"conversation_id": conversation_id, "role": role, "content": content})
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="メッセージの保存に失敗しました")
    return result.data[0]


def _touch_conversation(client: Client, conversation_id: str) -> None:
    client.table("conversations").update({"updated_at": "now()"}).eq(
        "id", conversation_id
    ).execute()


# ── Endpoints ────────────────────────────────────────────────


@app.post("/api/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation() -> ConversationResponse:
    client = get_supabase_client()
    row = await asyncio.to_thread(_insert_conversation, client)
    return ConversationResponse(**row)


@app.get("/api/conversations", response_model=list[ConversationResponse])
async def list_conversations() -> list[ConversationResponse]:
    client = get_supabase_client()
    rows = await asyncio.to_thread(_fetch_conversations, client)
    return [ConversationResponse(**r) for r in rows]


@app.get(
    "/api/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
async def list_messages(conversation_id: uuid.UUID) -> list[MessageResponse]:
    client = get_supabase_client()
    rows = await asyncio.to_thread(_fetch_messages, client, str(conversation_id))
    return [MessageResponse(**r) for r in rows]


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    client = get_supabase_client()

    if req.conversation_id is None:
        conv_row = await asyncio.to_thread(_insert_conversation, client)
        conv_id: str = conv_row["id"]
    else:
        conv_id = str(req.conversation_id)

    await asyncio.to_thread(_insert_message, client, conv_id, "user", req.message)

    reply: str = f"Pythonからの返信: {req.message}"

    await asyncio.to_thread(_insert_message, client, conv_id, "bot", reply)
    await asyncio.to_thread(_touch_conversation, client, conv_id)

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


app.mount(
    "/",
    StaticFiles(
        directory=Path(__file__).resolve().parent / "src" / "public", html=True
    ),
    name="static",
)
