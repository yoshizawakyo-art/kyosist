"""Playwright を使用してブラウザセッションを管理し、操作を実行するモジュール。"""

import base64
from typing import Any, Dict, Optional

try:
    from playwright.async_api import Browser, BrowserContext, Page, async_playwright
except ImportError:  # pragma: no cover - runtime dependency is optional in unit tests
    Browser = BrowserContext = Page = Any
    async_playwright = None


class BrowserExecutor:
    """ブラウザ操作を実行するクラス"""

    def __init__(self):
        """初期化"""
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def launch(self) -> None:
        """ブラウザを起動"""
        if async_playwright is None:
            raise RuntimeError("Playwright がインストールされていません")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
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
        if self.playwright:
            await self.playwright.stop()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    async def close_session(self) -> Dict[str, Any]:
        """ブラウザセッションを閉じる。"""
        await self.close()
        return {
            "status": "success",
            "action": "close_session",
            "message": "セッションを閉じました",
        }

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
                return await self.click(operation.get("selector", ""))
            elif action == "input_text":
                return await self.input_text(
                    operation.get("selector", ""), operation.get("text")
                )
            elif action == "scroll":
                return await self.scroll(
                    operation.get("direction", "down"), operation.get("amount", 100)
                )
            elif action == "navigate":
                return await self.navigate(operation.get("url", ""))
            elif action == "screenshot":
                return await self.screenshot()
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

    async def click(self, selector: str) -> Dict[str, Any]:
        """要素をクリック"""
        if not selector:
            return {
                "status": "error",
                "action": "click",
                "message": "selectorが指定されていません",
            }

        try:
            await self._ensure_browser()
            await self.page.click(selector)
            screenshot = await self._capture_screenshot()
            return {
                "status": "success",
                "action": "click",
                "selector": selector,
                "screenshot": screenshot,
                "message": f"要素 {selector} をクリックしました",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "click",
                "selector": selector,
                "message": f"クリック失敗: {str(exc)}",
            }

    async def input_text(self, selector: str, text: Any) -> Dict[str, Any]:
        """テキスト入力"""
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
            await self._ensure_browser()
            await self.page.fill(selector, str(text))
            screenshot = await self._capture_screenshot()
            return {
                "status": "success",
                "action": "input_text",
                "selector": selector,
                "text": str(text),
                "screenshot": screenshot,
                "message": f"要素 {selector} に入力しました",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "input_text",
                "selector": selector,
                "message": f"入力失敗: {str(exc)}",
            }

    async def scroll(
        self, direction: str = "down", amount: int = 100
    ) -> Dict[str, Any]:
        """スクロール"""
        try:
            await self._ensure_browser()
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

            screenshot = await self._capture_screenshot()
            return {
                "status": "success",
                "action": "scroll",
                "direction": direction,
                "amount": amount,
                "screenshot": screenshot,
                "message": f"{direction}方向に{amount}px スクロールしました",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "scroll",
                "message": f"スクロール失敗: {str(exc)}",
            }

    async def navigate(self, url: str) -> Dict[str, Any]:
        """ページナビゲーション"""
        if not url:
            return {
                "status": "error",
                "action": "navigate",
                "message": "URLが指定されていません",
            }

        try:
            await self._ensure_browser()
            await self.page.goto(url)
            screenshot = await self._capture_screenshot()
            return {
                "status": "success",
                "action": "navigate",
                "url": url,
                "screenshot": screenshot,
                "message": f"ページを {url} に移動しました",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "navigate",
                "url": url,
                "message": f"ナビゲーション失敗: {str(exc)}",
            }

    async def screenshot(self) -> Dict[str, Any]:
        """スクリーンショット（base64返却）"""
        try:
            await self._ensure_browser()
            screenshot_base64 = await self._capture_screenshot()
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

    async def _capture_screenshot(self) -> str:
        screenshot_bytes = await self.page.screenshot()
        return base64.b64encode(screenshot_bytes).decode("utf-8")
