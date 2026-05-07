"""
CLI コマンド実行（ホワイトリスト方式）のモジュール
許可されたコマンドのみを実行する
"""

import asyncio
import shlex
import time
from typing import Any, Dict


class CLIExecutor:
    """CLI コマンドを実行するクラス"""

    # ホワイトリスト
    ALLOWED_PATTERNS = {
        ("npm", "run", "build"),
        ("npm", "run", "dev"),
        ("npm", "test"),
        ("npm", "--version"),
        ("git", "status"),
        ("git", "log"),
        ("git", "diff"),
        ("python",),
        ("python3",),
        ("pip",),
        ("pip3",),
        ("ruff", "check"),
        ("ruff", "format"),
    }

    TIMEOUT_SECONDS = 30

    @staticmethod
    def _is_command_allowed(command: str) -> tuple[bool, str]:
        """
        コマンドが許可されているか確認

        Args:
            command: 実行するコマンド

        Returns:
            (allowed: bool, error_message: str)
        """
        if not command:
            return False, "コマンドが指定されていません"

        try:
            parts = shlex.split(command)
        except ValueError as exc:
            return False, f"コマンドの解析に失敗しました: {exc}"

        if not parts:
            return False, "コマンドが空です"

        for pattern in CLIExecutor.ALLOWED_PATTERNS:
            if tuple(parts[: len(pattern)]) == pattern:
                return True, ""

        allowed = ", ".join(" ".join(pattern) for pattern in sorted(CLIExecutor.ALLOWED_PATTERNS))
        if parts[0] not in {pattern[0] for pattern in CLIExecutor.ALLOWED_PATTERNS}:
            return False, f"未許可のコマンド: {parts[0]}。許可されたコマンド: {allowed}"

        return False, f"未許可の引数: {' '.join(parts[1:])}。許可されたコマンド: {allowed}"

    async def execute(self, command: str) -> Dict[str, Any]:
        """
        CLI コマンドを実行

        Args:
            command: 実行するコマンド

        Returns:
            実行結果。標準出力・標準エラー・終了コード・実行時間を含む。
        """
        allowed, error_msg = self._is_command_allowed(command)
        if not allowed:
            return {
                "status": "error",
                "command": command,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": 1,
                "duration_ms": 0,
            }

        start_time = time.time()
        try:
            parts = shlex.split(command)
            process = await asyncio.create_subprocess_exec(
                *parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # タイムアウト付きで待機
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                duration_ms = int((time.time() - start_time) * 1000)
                return {
                    "status": "error",
                    "command": command,
                    "stdout": "",
                    "stderr": f"タイムアウト（{self.TIMEOUT_SECONDS}秒）",
                    "exit_code": -1,
                    "duration_ms": duration_ms,
                }

            exit_code = process.returncode
            duration_ms = int((time.time() - start_time) * 1000)

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            status = "success" if exit_code == 0 else "error"

            return {
                "status": status,
                "command": command,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "exit_code": exit_code,
                "duration_ms": duration_ms,
            }
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "command": command,
                "stdout": "",
                "stderr": f"実行エラー: {str(exc)}",
                "exit_code": -1,
                "duration_ms": duration_ms,
            }
