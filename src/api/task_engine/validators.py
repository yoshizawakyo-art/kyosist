"""
セキュリティバリデーション機能
ユーザー入力・各エンジンの入力をバリデーションし、セキュリティ脅威を検出・ブロック
"""

import re
import shlex
from typing import Tuple


def validate_file_operation(path: str, action: str) -> Tuple[bool, str]:
    """
    ファイル操作のパスをバリデーション
    パストラバーサル、プロトコルハンドラ悪用を検出

    Args:
        path: ファイルパス
        action: 操作タイプ（read, write, delete）

    Returns:
        (成功, メッセージ) のタプル。成功時 True、検出時 False
    """
    if not path or not isinstance(path, str):
        return False, "パスが指定されていません"

    # パストラバーサル検出: ..
    if ".." in path:
        return False, "パストラバーサル検出: '..' が含まれています"

    # プロトコルハンドラ悪用検出
    dangerous_protocols = ["file:///", "ftp://", "gopher://", "ldap://", "telnet://"]
    for protocol in dangerous_protocols:
        if path.lower().startswith(protocol):
            return False, f"危険なプロトコル検出: '{protocol}'"

    # 相対パスの過度な使用を検出（複数の / からの遡上）
    if re.search(r"\.\./(\.\./)+", path):
        return False, "危険なパストラバーサルパターン検出"

    return True, ""


def validate_cli_command(command: str) -> Tuple[bool, str]:
    """
    CLIコマンドをバリデーション
    コマンドインジェクション、危険なコマンド実行を検出

    Args:
        command: 実行するコマンド文字列

    Returns:
        (成功, メッセージ) のタプル
    """
    if not command or not isinstance(command, str):
        return False, "コマンドが指定されていません"

    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return False, f"コマンド解析エラー: {exc}"
    allowed_prefixes = {
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
    if not any(tuple(parts[: len(prefix)]) == prefix for prefix in allowed_prefixes):
        return False, "危険または未許可の CLI コマンドです"

    # 危険なコマンドパターン検出
    dangerous_patterns = [
        (r";\s*(DROP|drop)", "SQL DROP 検出"),
        (r";\s*(rm|del|rmdir|format|erase)", "ファイル削除コマンド検出"),
        (r"\|\s*(cat|type|rm|del|rmdir)", "パイプによるコマンド注入検出"),
        (r"&&\s*(rm|del|rmdir|format|shutdown)", "&& による危険コマンド実行検出"),
        (r"\|\|\s*(rm|del|rmdir)", "|| による危険コマンド実行検出"),
        (r"&\s*(shutdown|reboot|poweroff)", "バックグラウンド危険コマンド検出"),
        (
            r"(curl|wget)\s+.*\|\s*(bash|sh|cmd|python)",
            "ネットワーク経由コード実行検出",
        ),
        (r"OR\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?", "SQL インジェクション"),
        (r"UNION\s+SELECT", "UNION SELECT インジェクション"),
        (r"(exec|execute|xp_cmdshell)", "DB プロシージャ実行"),
        (r"rm\s+-rf", "rm -rf コマンド検出"),
    ]

    for pattern, description in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"危険な CLI パターン検出: {description}"

    return True, ""


def validate_db_query(query: str, params: dict) -> Tuple[bool, str]:
    """
    SQLクエリをバリデーション
    SQLインジェクション、危険なステートメントを検出

    Args:
        query: SQL クエリ文字列
        params: バインドパラメータ（dict）

    Returns:
        (成功, メッセージ) のタプル
    """
    if not query or not isinstance(query, str):
        return False, "クエリが指定されていません"

    if not isinstance(params, dict):
        return False, "パラメータは dict である必要があります"

    # パラメータの型チェック（文字列のみ許可）
    for key, value in params.items():
        if value is not None and not isinstance(value, (str, int, float, bool)):
            return (
                False,
                f"パラメータ '{key}' の型が無効です（str, int, float, bool のみ許可）",
            )

    # 危険な SQL パターン検出
    dangerous_patterns = [
        (r"\bDROP\s+(TABLE|DATABASE|SCHEMA)", "DROP ステートメント検出"),
        (r"\bDELETE\s+FROM\s+\w+\s*;?\s*$", "全行削除 DELETE 検出"),
        (r"OR\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?", "OR 1=1 インジェクション"),
        (r"UNION\s+SELECT", "UNION SELECT インジェクション"),
        (r"\b(EXEC|EXECUTE)\s*\(", "EXEC/EXECUTE プロシージャ実行"),
        (r"xp_cmdshell", "SQL Server xp_cmdshell 実行"),
        (r"INTO\s+OUTFILE", "ファイル出力インジェクション"),
        (r";--", "SQL コメント注入"),
        (r"/\*.*\*/", "SQL ブロックコメント注入"),
    ]

    for pattern, description in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False, f"危険な SQL パターン検出: {description}"

    return True, ""


def validate_browser_selector(selector: str) -> Tuple[bool, str]:
    """
    CSS セレクタをバリデーション
    XSS ペイロード、悪意のある属性を検出

    Args:
        selector: CSS セレクタ文字列

    Returns:
        (成功, メッセージ) のタプル
    """
    if not selector or not isinstance(selector, str):
        return False, "セレクタが指定されていません"

    # XSS ペイロード検出
    dangerous_patterns = [
        (r"<script", "<script> タグ検出"),
        (r"javascript:", "javascript: プロトコルハンドラ検出"),
        (r"onerror\s*=", "onerror イベントハンドラ検出"),
        (r"onclick\s*=", "onclick イベントハンドラ検出"),
        (r"onload\s*=", "onload イベントハンドラ検出"),
        (r"onmouseover\s*=", "onmouseover イベントハンドラ検出"),
        (r"onfocus\s*=", "onfocus イベントハンドラ検出"),
        (r"onblur\s*=", "onblur イベントハンドラ検出"),
        (r"eval\s*\(", "eval() 関数検出"),
        (r"expression\s*\(", "CSS expression() 検出"),
        (r"<iframe", "<iframe> タグ検出"),
        (r"<object", "<object> タグ検出"),
        (r"<embed", "<embed> タグ検出"),
    ]

    for pattern, description in dangerous_patterns:
        if re.search(pattern, selector, re.IGNORECASE):
            return False, f"危険なセレクタパターン検出: {description}"

    return True, ""
