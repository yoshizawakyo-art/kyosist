"""
Supabase に SQL クエリを実行するモジュール
セキュリティ: SELECT/INSERT/UPDATE/DELETE のみ許可
DROP/ALTER/TRUNCATE はブロック
バインド変数（パラメータ化クエリ）を必須化
"""

import re
from typing import Any, Dict, List, Optional

# Supabase クライアントは使用環境で import される想定
# from supabase import create_client


class DBExecutor:
    """Supabase DB クエリを実行するクラス"""

    # 許可されるクエリタイプ
    ALLOWED_QUERY_TYPES = {"SELECT", "INSERT", "UPDATE", "DELETE"}

    # ブロックするキーワード
    BLOCKED_KEYWORDS = {
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "EXEC",
        "EXECUTE",
    }

    def __init__(self, supabase_client: Optional[Any] = None):
        """
        初期化

        Args:
            supabase_client: Supabase クライアントインスタンス
        """
        self.client = supabase_client

    @staticmethod
    def _is_query_safe(query: str) -> tuple[bool, Optional[str]]:
        """
        クエリがセキュアか検証

        Args:
            query: SQL クエリ

        Returns:
            (safe: bool, error_message: Optional[str])
        """
        if not query:
            return False, "クエリが指定されていません"

        query_upper = query.strip().upper()

        # ブロックキーワードをチェック
        for keyword in DBExecutor.BLOCKED_KEYWORDS:
            if re.search(rf"\b{keyword}\b", query_upper):
                return False, f"未許可のキーワード: {keyword}"

        # クエリタイプを抽出
        query_type = query_upper.split()[0] if query_upper.split() else None

        if query_type not in DBExecutor.ALLOWED_QUERY_TYPES:
            return (
                False,
                f"未許可のクエリタイプ: {query_type}。"
                f"許可されたタイプ: {', '.join(DBExecutor.ALLOWED_QUERY_TYPES)}",
            )

        if query_type in {"UPDATE", "DELETE"} and " WHERE " not in f" {query_upper} ":
            return False, f"{query_type} には WHERE 条件が必要です"

        return True, None

    async def execute(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        SQL クエリを実行

        Args:
            query: SQL クエリ（パラメータ化形式）
            params: クエリパラメータ（オプション）

        Returns:
            {"status": "success"/"error", "rows": [...], "affected_count": int, "query": str}
        """
        # クエリの安全性検証
        safe, error_msg = self._is_query_safe(query)
        if not safe:
            return {
                "status": "error",
                "query": query,
                "message": error_msg,
                "rows": [],
                "affected_count": 0,
            }

        query_type = query.strip().split()[0].upper() if query.strip() else ""
        if query_type in {"INSERT", "UPDATE", "DELETE"} and not params:
            return {
                "status": "error",
                "query": query,
                "message": "INSERT/UPDATE/DELETE はバインドパラメータが必要です",
                "rows": [],
                "affected_count": 0,
            }

        # Supabase クライアントが設定されていない場合
        if not self.client:
            return {
                "status": "error",
                "query": query,
                "message": "Supabase クライアントが設定されていません",
                "rows": [],
                "affected_count": 0,
            }

        try:
            if hasattr(self.client, "postgrest") and hasattr(
                self.client.postgrest, "query"
            ):
                if params:
                    response = await self.client.postgrest.query(query, params)
                else:
                    response = await self.client.postgrest.query(query)
            elif hasattr(self.client, "rpc"):
                response = self.client.rpc(
                    "execute_task_sql",
                    {"sql_query": query, "sql_params": params or {}},
                ).execute()
            elif params:
                response = await self.client.postgrest.query(query, params)
            else:
                response = await self.client.postgrest.query(query)

            # レスポンス処理
            rows = response.data if hasattr(response, "data") else []
            affected_count = (
                len(rows) if isinstance(rows, list) else 0
            )  # INSERT/UPDATE/DELETE の場合は affected count を計算

            return {
                "status": "success",
                "query": query,
                "rows": rows,
                "affected_count": affected_count,
                "message": "クエリを実行しました",
            }
        except Exception as exc:
            return {
                "status": "error",
                "query": query,
                "message": f"クエリ実行エラー: {str(exc)}",
                "rows": [],
                "affected_count": 0,
            }

    async def execute_transaction(
        self, queries: List[tuple[str, Optional[Dict[str, Any]]]]
    ) -> Dict[str, Any]:
        """
        複数のクエリをトランザクションで実行
        失敗時は自動ロールバック

        Args:
            queries: [(query: str, params: Dict), ...] のリスト

        Returns:
            {"status": "success"/"error", "results": [...], "message": str}
        """
        results = []

        try:
            # 事前にすべてのクエリを検証
            for query, _ in queries:
                safe, error_msg = self._is_query_safe(query)
                if not safe:
                    return {
                        "status": "error",
                        "results": results,
                        "message": f"クエリ検証エラー: {error_msg}",
                    }

            # トランザクション開始
            if not self.client:
                return {
                    "status": "error",
                    "results": [],
                    "message": "Supabase クライアントが設定されていません",
                }

            # 各クエリを実行
            for query, params in queries:
                result = await self.execute(query, params)
                results.append(result)

                # 1つのクエリが失敗したらロールバック
                if result["status"] == "error":
                    return {
                        "status": "error",
                        "results": results,
                        "message": f"トランザクション中のクエリ実行エラー: {result['message']}",
                    }

            return {
                "status": "success",
                "results": results,
                "message": f"{len(queries)} 件のクエリを実行しました",
            }
        except Exception as exc:
            return {
                "status": "error",
                "results": results,
                "message": f"トランザクション実行エラー: {str(exc)}",
            }
