"""
browser_executor.py のテストモジュール
"""

import pytest
import tempfile
from pathlib import Path

from api.task_engine.browser_executor import BrowserExecutor


@pytest.fixture
def temp_html():
    """テスト用の一時HTML ファイルを生成"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <input id="email" type="email" placeholder="メール">
        <input id="password" type="password" placeholder="パスワード">
        <button id="submit-btn">送信</button>
        <div id="result" style="display:none;">成功しました</div>
    </body>
    </html>
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html_content)
        temp_path = f.name

    yield Path(temp_path).as_uri()

    # クリーンアップ
    Path(temp_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_browser_navigate(temp_html):
    """ナビゲーション操作をテスト"""
    executor = BrowserExecutor()
    try:
        result = await executor.execute({"action": "navigate", "url": temp_html})
        assert result["status"] == "success"
        assert result["action"] == "navigate"
        assert result["url"] == temp_html
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_browser_click(temp_html):
    """クリック操作をテスト"""
    executor = BrowserExecutor()
    try:
        await executor.execute({"action": "navigate", "url": temp_html})
        result = await executor.execute({"action": "click", "selector": "#submit-btn"})
        assert result["status"] == "success"
        assert result["action"] == "click"
        assert result["selector"] == "#submit-btn"
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_browser_input_text(temp_html):
    """テキスト入力操作をテスト"""
    executor = BrowserExecutor()
    try:
        await executor.execute({"action": "navigate", "url": temp_html})
        result = await executor.execute(
            {"action": "input_text", "selector": "#email", "text": "test@example.com"}
        )
        assert result["status"] == "success"
        assert result["action"] == "input_text"
        assert result["selector"] == "#email"
        assert result["text"] == "test@example.com"
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_browser_screenshot(temp_html):
    """スクリーンショット操作をテスト"""
    executor = BrowserExecutor()
    try:
        await executor.execute({"action": "navigate", "url": temp_html})
        result = await executor.execute({"action": "screenshot"})
        assert result["status"] == "success"
        assert result["action"] == "screenshot"
        assert "screenshot" in result
        assert len(result["screenshot"]) > 0
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_browser_scroll(temp_html):
    """スクロール操作をテスト"""
    executor = BrowserExecutor()
    try:
        await executor.execute({"action": "navigate", "url": temp_html})
        result = await executor.execute(
            {"action": "scroll", "direction": "down", "amount": 100}
        )
        assert result["status"] == "success"
        assert result["action"] == "scroll"
        assert result["direction"] == "down"
        assert result["amount"] == 100
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_browser_click_missing_selector():
    """selectorなしのクリック操作はエラーを返す"""
    executor = BrowserExecutor()
    try:
        result = await executor.execute({"action": "click"})
        assert result["status"] == "error"
        assert "selectorが指定されていません" in result["message"]
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_browser_input_missing_text():
    """textなしの入力操作はエラーを返す"""
    executor = BrowserExecutor()
    try:
        result = await executor.execute({"action": "input_text", "selector": "#email"})
        assert result["status"] == "error"
        assert "textが指定されていません" in result["message"]
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_browser_unsupported_action():
    """未サポートの操作はエラーを返す"""
    executor = BrowserExecutor()
    try:
        result = await executor.execute({"action": "unknown_action"})
        assert result["status"] == "error"
        assert "未サポートの操作" in result["message"]
    finally:
        await executor.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
