"""
CLI コマンド実行（ホワイトリスト方式）のモジュール
許可されたコマンドのみを実行する
"""

import asyncio
import time
from typing import Any, Dict


class CLIExecutor:
    """CLI コマンドを実行するクラス"""

    # ホワイトリスト
    ALLOWED_COMMANDS = {
        "npm": ["run", "build", "dev", "test", "install"],
        "git": ["status", "log", "diff", "add", "commit", "push", "pull"],
        "python": [],  # すべてのpython引数を許可
        "pip": ["install", "list", "show"],
        "ruff": ["check", "format"],
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

        parts = command.strip().split()
        if not parts:
            return False, "コマンドが空です"

        base_cmd = parts[0]

        # ホワイトリストに存在しないコマンド
        if base_cmd not in CLIExecutor.ALLOWED_COMMANDS:
            return (
                False,
                f"未許可のコマンド: {base_cmd}。"
                f"許可されたコマンド: {', '.join(CLIExecutor.ALLOWED_COMMANDS.keys())}",
            )

        allowed_args = CLIExecutor.ALLOWED_COMMANDS[base_cmd]

        # 引数チェック（許可リストが空でない場合）
        if allowed_args and len(parts) > 1:
            first_arg = parts[1]
            if first_arg not in allowed_args:
                return (
                    False,
                    f"未許可の引数: {first_arg}。"
                    f"許可されたコマンド: {base_cmd} {', '.join(allowed_args)}",
                )

        return True, ""

    async def execute(self, command: str) -> Dict[str, Any]:
        """
        CLI コマンドを実行

        Args:
            command: 実行するコマンド

        Returns:
            {"status": "success"/"error", "command": str, "stdout": str, "stderr": str, "exit_code": int, "duration_ms": int}
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
            # asyncio.create_subprocess_shell を使用
            process = await asyncio.create_subprocess_shell(
                command,
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
