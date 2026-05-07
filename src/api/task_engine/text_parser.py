"""
自然言語タスク指示をパースして操作タイプとパラメータに変換するモジュール
"""

import re
from typing import Any, Dict


def parse_task_input(user_input: str) -> Dict[str, Any]:
    """
    ユーザーの自然言語指示をパースして、操作タイプとパラメータに変換する。

    Args:
        user_input: ユーザーからの自然言語指示

    Returns:
        {"task_type": str, "action": str, "params": dict} または {"error": str}
    """
    if not user_input or not isinstance(user_input, str):
        return {"error": "入力が空か無効です"}

    user_input = user_input.strip()

    # ファイル操作パターン
    file_create_match = re.match(
        r"ファイル\s+(.+?)\s+を作成して内容:\s+(.+)$", user_input
    )
    if file_create_match:
        path = file_create_match.group(1).strip()
        content = file_create_match.group(2).strip()
        return {
            "task_type": "file",
            "action": "create",
            "params": {"path": path, "content": content},
        }

    file_edit_match = re.match(
        r"ファイル\s+(.+?)\s+を編集して内容:\s+(.+)$", user_input
    )
    if file_edit_match:
        path = file_edit_match.group(1).strip()
        content = file_edit_match.group(2).strip()
        return {
            "task_type": "file",
            "action": "edit",
            "params": {"path": path, "content": content},
        }

    file_delete_match = re.match(r"ファイル\s+(.+?)\s+を削除して$", user_input)
    if file_delete_match:
        path = file_delete_match.group(1).strip()
        return {
            "task_type": "file",
            "action": "delete",
            "params": {"path": path},
        }

    file_read_match = re.match(r"ファイル\s+(.+?)\s+を読んで$", user_input)
    if file_read_match:
        path = file_read_match.group(1).strip()
        return {
            "task_type": "file",
            "action": "read",
            "params": {"path": path},
        }

    # CLI コマンド実行パターン
    cli_match = re.match(r"コマンド実行:\s+(.+)$", user_input)
    if cli_match:
        command = cli_match.group(1).strip()
        return {
            "task_type": "cli",
            "action": "execute",
            "params": {"command": command},
        }

    # ブラウザ操作パターン
    browser_click_match = re.match(r"ブラウザ操作:\s+クリック\s+(.+)$", user_input)
    if browser_click_match:
        selector = browser_click_match.group(1).strip()
        return {
            "task_type": "browser",
            "action": "click",
            "params": {"selector": selector},
        }

    browser_input_match = re.match(
        r"ブラウザ操作:\s+入力フォーム\s+(.+?)\s+に\s+(.+?)\s+を入力$",
        user_input,
    )
    if browser_input_match:
        selector = browser_input_match.group(1).strip()
        text = browser_input_match.group(2).strip()
        return {
            "task_type": "browser",
            "action": "input_text",
            "params": {"selector": selector, "text": text},
        }

    browser_navigate_match = re.match(r"ブラウザ操作:\s+移動\s+(.+)$", user_input)
    if browser_navigate_match:
        url = browser_navigate_match.group(1).strip()
        return {
            "task_type": "browser",
            "action": "navigate",
            "params": {"url": url},
        }

    browser_scroll_match = re.match(
        r"ブラウザ操作:\s+スクロール\s+(down|up|left|right)(?:\s+(\d+))?$",
        user_input,
    )
    if browser_scroll_match:
        return {
            "task_type": "browser",
            "action": "scroll",
            "params": {
                "direction": browser_scroll_match.group(1),
                "amount": int(browser_scroll_match.group(2) or 100),
            },
        }

    if re.match(r"ブラウザ操作:\s+スクリーンショット$", user_input):
        return {
            "task_type": "browser",
            "action": "screenshot",
            "params": {},
        }

    # DB実行パターン
    db_match = re.match(r"DB実行:\s+(.+)$", user_input)
    if db_match:
        query = db_match.group(1).strip()
        return {
            "task_type": "db",
            "action": "execute",
            "params": {"query": query},
        }

    # マッチしなかった場合
    return {"error": f"パースできない指示形式です: {user_input}"}
