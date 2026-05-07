"""
Playwr ightを使用してブラウザセッションを管理し、操作を実行するモジュール
"""

import base64
from typing import Any, Dict, Optional

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class BrowserExecutor:
    """ブラウザ操作を実行するクラス"""

    def __init__(self):
        """初期化"""
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def launch(self) -> None:
        """ブラウザを起動"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def close(self) -> None:
        """ブラウザを閉じる"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def _ensure_browser(self) -> None:
        """ブラウザが起動していることを確認"""
        if not self.page:
            await self.launch()

    async def execute(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        ブラウザ操作を実行

        Args:
            operation: 操作情報 {"action": "click", "selector": "..."}

        Returns:
            {"status": "success"/"error", "action": "...", ...}
        """
        try:
            await self._ensure_browser()

            action = operation.get("action")

            if action == "click":
                return await self._click(operation)
            elif action == "input_text":
                return await self._input_text(operation)
            elif action == "scroll":
                return await self._scroll(operation)
            elif action == "navigate":
                return await self._navigate(operation)
            elif action == "screenshot":
                return await self._screenshot(operation)
            else:
                return {
                    "status": "error",
                    "action": action,
                    "message": f"未サポートの操作: {action}",
                }
        except Exception as exc:
            return {
                "status": "error",
                "action": operation.get("action"),
                "message": f"エラー発生: {str(exc)}",
            }

    async def _click(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """要素をクリック"""
        selector = operation.get("selector")
        if not selector:
            return {
                "status": "error",
                "action": "click",
                "message": "selectorが指定されていません",
            }

        try:
            await self.page.click(selector)
            return {
                "status": "success",
                "action": "click",
                "selector": selector,
                "message": f"要素 {selector} をクリックしました",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "click",
                "selector": selector,
                "message": f"クリック失敗: {str(exc)}",
            }

    async def _input_text(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """テキスト入力"""
        selector = operation.get("selector")
        text = operation.get("text")

        if not selector:
            return {
                "status": "error",
                "action": "input_text",
                "message": "selectorが指定されていません",
            }
        if text is None:
            return {
                "status": "error",
                "action": "input_text",
                "message": "textが指定されていません",
            }

        try:
            await self.page.fill(selector, str(text))
            return {
                "status": "success",
                "action": "input_text",
                "selector": selector,
                "text": str(text),
                "message": f"要素 {selector} に入力しました",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "input_text",
                "selector": selector,
                "message": f"入力失敗: {str(exc)}",
            }

    async def _scroll(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """スクロール"""
        direction = operation.get("direction", "down")
        amount = operation.get("amount", 100)

        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == "right":
                await self.page.evaluate(f"window.scrollBy({amount}, 0)")
            elif direction == "left":
                await self.page.evaluate(f"window.scrollBy(-{amount}, 0)")
            else:
                return {
                    "status": "error",
                    "action": "scroll",
                    "message": f"未サポートの方向: {direction}",
                }

            return {
                "status": "success",
                "action": "scroll",
                "direction": direction,
                "amount": amount,
                "message": f"{direction}方向に{amount}px スクロールしました",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "scroll",
                "message": f"スクロール失敗: {str(exc)}",
            }

    async def _navigate(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """ページナビゲーション"""
        url = operation.get("url")
        if not url:
            return {
                "status": "error",
                "action": "navigate",
                "message": "URLが指定されていません",
            }

        try:
            await self.page.goto(url)
            return {
                "status": "success",
                "action": "navigate",
                "url": url,
                "message": f"ページを {url} に移動しました",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "navigate",
                "url": url,
                "message": f"ナビゲーション失敗: {str(exc)}",
            }

    async def _screenshot(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """スクリーンショット（base64返却）"""
        try:
            screenshot_bytes = await self.page.screenshot()
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            return {
                "status": "success",
                "action": "screenshot",
                "screenshot": screenshot_base64,
                "message": "スクリーンショットを取得しました",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "screenshot",
                "message": f"スクリーンショット取得失敗: {str(exc)}",
            }
