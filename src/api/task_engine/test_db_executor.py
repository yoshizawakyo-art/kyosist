"""
db_executor.py のテストモジュール
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from db_executor import DBExecutor


@pytest.mark.asyncio
async def test_db_query_safe_select():
    """SELECT クエリは許可される"""
    executor = DBExecutor()
    safe, error = executor._is_query_safe("SELECT * FROM users WHERE id = 1")
    assert safe is True
    assert error is None


@pytest.mark.asyncio
async def test_db_query_safe_insert():
    """INSERT クエリは許可される"""
    executor = DBExecutor()
    safe, error = executor._is_query_safe("INSERT INTO users (name) VALUES (?)")
    assert safe is True
    assert error is None


@pytest.mark.asyncio
async def test_db_query_safe_update():
    """UPDATE クエリは許可される"""
    executor = DBExecutor()
    safe, error = executor._is_query_safe("UPDATE users SET name = ? WHERE id = 1")
    assert safe is True
    assert error is None


@pytest.mark.asyncio
async def test_db_query_safe_delete():
    """DELETE クエリは許可される"""
    executor = DBExecutor()
    safe, error = executor._is_query_safe("DELETE FROM users WHERE id = 1")
    assert safe is True
    assert error is None


@pytest.mark.asyncio
async def test_db_query_unsafe_drop():
    """DROP クエリはブロックされる"""
    executor = DBExecutor()
    safe, error = executor._is_query_safe("DROP TABLE users")
    assert safe is False
    assert "未許可のキーワード" in error


@pytest.mark.asyncio
async def test_db_query_unsafe_alter():
    """ALTER クエリはブロックされる"""
    executor = DBExecutor()
    safe, error = executor._is_query_safe("ALTER TABLE users ADD COLUMN age INT")
    assert safe is False
    assert "未許可のキーワード" in error


@pytest.mark.asyncio
async def test_db_query_unsafe_truncate():
    """TRUNCATE クエリはブロックされる"""
    executor = DBExecutor()
    safe, error = executor._is_query_safe("TRUNCATE TABLE users")
    assert safe is False
    assert "未許可のキーワード" in error


@pytest.mark.asyncio
async def test_db_query_unsafe_create():
    """CREATE クエリはブロックされる"""
    executor = DBExecutor()
    safe, error = executor._is_query_safe("CREATE TABLE users (id INT)")
    assert safe is False
    assert "未許可のキーワード" in error


@pytest.mark.asyncio
async def test_db_execute_without_client():
    """クライアントが設定されていない場合はエラー"""
    executor = DBExecutor(supabase_client=None)
    result = await executor.execute("SELECT * FROM users")

    assert result["status"] == "error"
    assert "Supabase クライアントが設定されていません" in result["message"]


@pytest.mark.asyncio
async def test_db_execute_with_mock_client():
    """モッククライアントでクエリ実行"""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.data = [{"id": 1, "name": "Test User"}]
    mock_client.postgrest.query = AsyncMock(return_value=mock_response)

    executor = DBExecutor(supabase_client=mock_client)
    result = await executor.execute("SELECT * FROM users")

    assert result["status"] == "success"
    assert result["query"] == "SELECT * FROM users"
    assert len(result["rows"]) == 1
    assert result["affected_count"] == 1


@pytest.mark.asyncio
async def test_db_execute_empty_query():
    """空のクエリはエラーを返す"""
    executor = DBExecutor()
    result = await executor.execute("")

    assert result["status"] == "error"
    assert "クエリが指定されていません" in result["message"]


@pytest.mark.asyncio
async def test_db_execute_invalid_query_type():
    """未許可のクエリタイプはエラーを返す"""
    executor = DBExecutor()
    result = await executor.execute("CREATE TABLE users (id INT)")

    assert result["status"] == "error"
    assert "未許可のキーワード" in result["message"]


@pytest.mark.asyncio
async def test_db_transaction_success():
    """トランザクション実行成功"""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.data = []
    mock_client.postgrest.query = AsyncMock(return_value=mock_response)

    executor = DBExecutor(supabase_client=mock_client)
    queries = [
        ("INSERT INTO users (name) VALUES (?)", {"name": "User1"}),
        ("SELECT * FROM users", None),
    ]

    result = await executor.execute_transaction(queries)

    assert result["status"] == "success"
    assert len(result["results"]) == 2


@pytest.mark.asyncio
async def test_db_transaction_fail_on_invalid_query():
    """トランザクションの検証失敗"""
    executor = DBExecutor()
    queries = [
        ("SELECT * FROM users", None),
        ("DROP TABLE users", None),  # この行で失敗
    ]

    result = await executor.execute_transaction(queries)

    assert result["status"] == "error"
    assert "クエリ検証エラー" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
