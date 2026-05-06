import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from api.index import (
    _build_chat_prompt,
    _fetch_conversations,
    _fetch_messages,
    _insert_conversation,
    _insert_message,
    get_supabase_client,
)
from api.agent_service import (
    create_gemini_client,
    generate_gemini_text,
    get_gemini_model,
    stream_gemini_text,
)


class FakeResult:
    def __init__(self, data):
        self.data = data


class FakeTable:
    def __init__(self, data=None, exc=None):
        self.data = data
        self.exc = exc
        self.insert_payload = None
        self.filters = []

    def insert(self, payload):
        self.insert_payload = payload
        return self

    def select(self, _columns):
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, _limit):
        return self

    def execute(self):
        if self.exc:
            raise self.exc
        return FakeResult(self.data)


class FakeClient:
    def __init__(self, table):
        self.last_table = None
        self.table_obj = table

    def table(self, table_name):
        self.last_table = table_name
        return self.table_obj


class FakeGeminiModels:
    def __init__(self):
        self.generate_args = None
        self.stream_args = None

    async def generate_content(self, **kwargs):
        self.generate_args = kwargs
        return SimpleNamespace(text="応答")

    async def generate_content_stream(self, **kwargs):
        self.stream_args = kwargs

        async def chunks():
            yield SimpleNamespace(text="A")
            yield SimpleNamespace(text="")
            yield SimpleNamespace(text="B")

        return chunks()


class FakeGeminiClient:
    def __init__(self):
        self.models = FakeGeminiModels()
        self.aio = SimpleNamespace(models=self.models)


class ChatDbHelperTests(unittest.TestCase):
    def test_get_supabase_client_reports_missing_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(HTTPException) as raised:
                get_supabase_client()

        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("データベース接続設定", raised.exception.detail)

    def test_insert_conversation_requires_user_id(self):
        with self.assertRaises(HTTPException) as raised:
            _insert_conversation(FakeClient(FakeTable()), None)

        self.assertEqual(raised.exception.status_code, 400)

    def test_insert_conversation_scopes_payload_to_user(self):
        table = FakeTable(data=[{"id": "conversation-1", "user_id": "user-1"}])
        row = _insert_conversation(FakeClient(table), "user-1")

        self.assertEqual(row["id"], "conversation-1")
        self.assertEqual(table.insert_payload, {"user_id": "user-1"})

    def test_insert_message_empty_response_is_service_unavailable(self):
        with self.assertRaises(HTTPException) as raised:
            _insert_message(
                FakeClient(FakeTable(data=[])), "conversation-1", "user", "hi"
            )

        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("メッセージを保存", raised.exception.detail)

    def test_fetch_conversations_returns_empty_list_for_empty_database_response(self):
        table = FakeTable(data=None)
        rows = _fetch_conversations(FakeClient(table), "user-1")

        self.assertEqual(rows, [])
        self.assertIn(("user_id", "user-1"), table.filters)

    def test_fetch_messages_database_exception_is_user_friendly(self):
        with self.assertRaises(HTTPException) as raised:
            _fetch_messages(
                FakeClient(FakeTable(exc=RuntimeError("boom"))), "conversation-1"
            )

        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("メッセージ履歴を読み込めません", raised.exception.detail)

    def test_chat_prompt_preserves_roles_for_gemini(self):
        prompt = _build_chat_prompt(
            [
                {"role": "user", "content": "こんにちは"},
                {"role": "bot", "content": "どうしましたか？"},
            ],
            "予定を整理して",
        )

        self.assertIn("User: こんにちは", prompt)
        self.assertIn("Assistant: どうしましたか？", prompt)
        self.assertTrue(prompt.endswith("Assistant:"))

    def test_gemini_model_defaults_to_flash_lite(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_gemini_model(), "gemini-2.5-flash-lite")

    def test_create_gemini_client_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as raised:
                create_gemini_client()

        self.assertIn("GEMINI_API_KEY", str(raised.exception))

    def test_generate_gemini_text_uses_configured_model(self):
        client = FakeGeminiClient()
        with patch.dict(os.environ, {"GEMINI_MODEL": "custom-gemini-model"}):
            text = asyncio_run(generate_gemini_text(client, "prompt", temperature=0.2))

        self.assertEqual(text, "応答")
        self.assertEqual(client.models.generate_args["model"], "custom-gemini-model")
        self.assertEqual(client.models.generate_args["contents"], "prompt")
        self.assertEqual(client.models.generate_args["config"]["temperature"], 0.2)

    def test_stream_gemini_text_filters_empty_chunks(self):
        client = FakeGeminiClient()

        async def collect():
            return [chunk async for chunk in stream_gemini_text(client, "prompt")]

        self.assertEqual(asyncio_run(collect()), ["A", "B"])


def asyncio_run(coro):
    import asyncio

    return asyncio.run(coro)


if __name__ == "__main__":
    unittest.main()
