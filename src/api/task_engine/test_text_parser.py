"""
text_parser.py のテストモジュール
"""

import pytest
from api.task_engine.text_parser import parse_task_input


def test_parse_file_create():
    """ファイル作成指示をパースする"""
    result = parse_task_input("ファイル /tmp/test.txt を作成して内容: Hello World")
    assert result["task_type"] == "file"
    assert result["action"] == "create"
    assert result["params"]["path"] == "/tmp/test.txt"
    assert result["params"]["content"] == "Hello World"


def test_parse_file_edit():
    """ファイル編集指示をパースする"""
    result = parse_task_input("ファイル /tmp/test.txt を編集して内容: Updated Content")
    assert result["task_type"] == "file"
    assert result["action"] == "edit"
    assert result["params"]["path"] == "/tmp/test.txt"
    assert result["params"]["content"] == "Updated Content"


def test_parse_file_delete():
    """ファイル削除指示をパースする"""
    result = parse_task_input("ファイル /tmp/test.txt を削除して")
    assert result["task_type"] == "file"
    assert result["action"] == "delete"
    assert result["params"]["path"] == "/tmp/test.txt"


def test_parse_cli_command():
    """CLI実行指示をパースする"""
    result = parse_task_input("コマンド実行: npm run build")
    assert result["task_type"] == "cli"
    assert result["action"] == "execute"
    assert result["params"]["command"] == "npm run build"


def test_parse_browser_click():
    """ブラウザクリック指示をパースする"""
    result = parse_task_input("ブラウザ操作: クリック #submit-btn")
    assert result["task_type"] == "browser"
    assert result["action"] == "click"
    assert result["params"]["selector"] == "#submit-btn"


def test_parse_browser_input():
    """ブラウザテキスト入力指示をパースする"""
    result = parse_task_input(
        "ブラウザ操作: 入力フォーム #email に test@example.com を入力"
    )
    assert result["task_type"] == "browser"
    assert result["action"] == "input_text"
    assert result["params"]["selector"] == "#email"
    assert result["params"]["text"] == "test@example.com"


def test_parse_db_query():
    """DB実行指示をパースする"""
    result = parse_task_input("DB実行: SELECT * FROM users WHERE id = 1")
    assert result["task_type"] == "db"
    assert result["action"] == "execute"
    assert result["params"]["query"] == "SELECT * FROM users WHERE id = 1"


def test_parse_invalid_input():
    """無効な指示をパースするとエラーを返す"""
    result = parse_task_input("これは何の指示でもありません")
    assert "error" in result
    assert "パースできない指示形式" in result["error"]


def test_parse_empty_input():
    """空の入力をパースするとエラーを返す"""
    result = parse_task_input("")
    assert "error" in result


def test_parse_none_input():
    """None入力をパースするとエラーを返す"""
    result = parse_task_input(None)
    assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
