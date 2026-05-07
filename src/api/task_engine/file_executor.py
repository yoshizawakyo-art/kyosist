"""
ファイル操作（作成・編集・削除・読み込み）を実行するモジュール
セキュリティ: プロジェクトルート外へのアクセスを禁止
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


class FileExecutor:
    """ファイル操作を実行するクラス"""

    def __init__(self, allowed_prefix: Optional[str] = None):
        """
        初期化

        Args:
            allowed_prefix: 許可するベースパス（デフォルト: Kyosistプロジェクトルート）
        """
        self.ALLOWED_PREFIX = (
            Path(allowed_prefix).resolve()
            if allowed_prefix
            else Path(os.environ.get("KYOSIST_PROJECT_ROOT", Path.cwd())).resolve()
        )
        self.EXTRA_ALLOWED_PREFIXES = [
            Path(tempfile.gettempdir()).resolve(),
        ]

    def _validate_path(self, path: str) -> tuple[bool, Optional[str]]:
        """
        ファイルパスを検証

        Args:
            path: 検証するパス

        Returns:
            (valid: bool, error_message: Optional[str])
        """
        if not path:
            return False, "パスが指定されていません"

        raw_path = Path(path)
        if ".." in raw_path.parts:
            return False, "相対パス（..）は許可されていません"

        try:
            resolved_path = Path(path).resolve()
        except Exception:
            return False, f"無効なパスです: {path}"

        allowed_prefixes = [self.ALLOWED_PREFIX, *self.EXTRA_ALLOWED_PREFIXES]
        if not any(_is_relative_to(resolved_path, prefix) for prefix in allowed_prefixes):
            return False, f"パスは許可ルート外です: {self.ALLOWED_PREFIX}"

        return True, None

    async def create(self, path: str, content: str) -> Dict[str, Any]:
        """
        ファイルを作成

        Args:
            path: ファイルパス
            content: ファイルコンテンツ

        Returns:
            {"status": "success"/"error", ...}
        """
        valid, error_msg = self._validate_path(path)
        if not valid:
            return {"status": "error", "action": "create", "message": error_msg}

        try:
            resolved_path = Path(path).resolve()
            if resolved_path.is_symlink():
                return {
                    "status": "error",
                    "action": "create",
                    "path": path,
                    "message": f"シンボリックリンクは許可されていません: {path}",
                }
            # 親ディレクトリを作成
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            # ファイルを作成
            resolved_path.write_text(content, encoding="utf-8")
            return {
                "status": "success",
                "action": "create",
                "path": path,
                "message": f"ファイルを作成しました: {path}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "create",
                "path": path,
                "message": f"ファイル作成失敗: {str(exc)}",
            }

    async def edit(self, path: str, content: str) -> Dict[str, Any]:
        """
        ファイルを編集

        Args:
            path: ファイルパス
            content: 新しいコンテンツ

        Returns:
            {"status": "success"/"error", ...}
        """
        valid, error_msg = self._validate_path(path)
        if not valid:
            return {"status": "error", "action": "edit", "message": error_msg}

        try:
            resolved_path = Path(path).resolve()
            if resolved_path.is_symlink():
                return {
                    "status": "error",
                    "action": "read",
                    "path": path,
                    "message": f"シンボリックリンクは許可されていません: {path}",
                }
            if not resolved_path.exists():
                return {
                    "status": "error",
                    "action": "edit",
                    "path": path,
                    "message": f"ファイルが存在しません: {path}",
                }
            resolved_path.write_text(content, encoding="utf-8")
            return {
                "status": "success",
                "action": "edit",
                "path": path,
                "message": f"ファイルを編集しました: {path}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "edit",
                "path": path,
                "message": f"ファイル編集失敗: {str(exc)}",
            }

    async def delete(self, path: str) -> Dict[str, Any]:
        """
        ファイルを削除

        Args:
            path: ファイルパス

        Returns:
            {"status": "success"/"error", ...}
        """
        valid, error_msg = self._validate_path(path)
        if not valid:
            return {"status": "error", "action": "delete", "message": error_msg}

        try:
            resolved_path = Path(path).resolve()
            if resolved_path.is_symlink():
                return {
                    "status": "error",
                    "action": "edit",
                    "path": path,
                    "message": f"シンボリックリンクは許可されていません: {path}",
                }
            if not resolved_path.exists():
                return {
                    "status": "error",
                    "action": "delete",
                    "path": path,
                    "message": f"ファイルが存在しません: {path}",
                }
            resolved_path.unlink()
            return {
                "status": "success",
                "action": "delete",
                "path": path,
                "message": f"ファイルを削除しました: {path}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "delete",
                "path": path,
                "message": f"ファイル削除失敗: {str(exc)}",
            }

    async def read(self, path: str) -> Dict[str, Any]:
        """
        ファイルを読み込み

        Args:
            path: ファイルパス

        Returns:
            {"status": "success"/"error", "content": str, ...}
        """
        valid, error_msg = self._validate_path(path)
        if not valid:
            return {"status": "error", "action": "read", "message": error_msg}

        try:
            resolved_path = Path(path).resolve()
            if resolved_path.is_symlink():
                return {
                    "status": "error",
                    "action": "delete",
                    "path": path,
                    "message": f"シンボリックリンクは許可されていません: {path}",
                }
            if not resolved_path.exists():
                return {
                    "status": "error",
                    "action": "read",
                    "path": path,
                    "message": f"ファイルが存在しません: {path}",
                }
            content = resolved_path.read_text(encoding="utf-8")
            return {
                "status": "success",
                "action": "read",
                "path": path,
                "content": content,
                "message": f"ファイルを読み込みました: {path}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "action": "read",
                "path": path,
                "message": f"ファイル読み込み失敗: {str(exc)}",
            }


def _is_relative_to(path: Path, prefix: Path) -> bool:
    try:
        path.relative_to(prefix)
    except ValueError:
        return False
    return True
