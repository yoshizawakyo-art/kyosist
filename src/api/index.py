import asyncio
import os
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import Client, create_client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "public"), html=True),
    name="static",
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
