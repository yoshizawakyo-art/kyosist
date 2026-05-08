"""
タスク実行 API エンドポイント
- ユーザープロフィール管理
- タスク実行・履歴管理
- スキル管理
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from supabase import create_client

from api.task_engine import text_parser, validators
from api.task_engine.browser_executor import BrowserExecutor
from api.task_engine.cli_executor import CLIExecutor
from api.task_engine.db_executor import DBExecutor
from api.task_engine.file_executor import FileExecutor

# ============================================================================
# Pydantic モデル
# ============================================================================


class UserProfileRequest(BaseModel):
    """ユーザープロフィール作成・更新リクエスト"""

    username: str


class UserProfileResponse(BaseModel):
    """ユーザープロフィール レスポンス"""

    id: str
    user_id: str
    username: str


class ExecuteTaskRequest(BaseModel):
    """タスク実行リクエスト"""

    user_input: str


class ExecuteTaskResponse(BaseModel):
    """タスク実行 レスポンス"""

    id: str
    status: str
    task_type: str
    result: Dict[str, Any]
    created_at: str


class TaskHistoryItem(BaseModel):
    """履歴アイテム"""

    id: str
    task_type: str
    task_input: str
    status: str
    created_at: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskHistoryCreateRequest(BaseModel):
    """履歴保存リクエスト"""

    task_type: str
    task_input: str
    status: str
    result: Dict[str, Any] = {}
    executed_command: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class SkillPatternRequest(BaseModel):
    """スキルパターン"""

    task_type: str
    action: str
    params: Dict[str, Any]


class SkillCreateRequest(BaseModel):
    """スキル作成リクエスト"""

    skill_name: str
    description: str
    pattern: SkillPatternRequest


class SkillResponse(BaseModel):
    """スキル レスポンス"""

    id: str
    skill_name: str
    description: str
    pattern: Dict[str, Any]
    created_at: str


# ============================================================================
# ルーター
# ============================================================================

router = APIRouter(prefix="/api", tags=["tasks"])

_IN_MEMORY_PROFILES: Dict[str, Dict[str, Any]] = {}
_IN_MEMORY_HISTORY: Dict[str, List[Dict[str, Any]]] = {}
_IN_MEMORY_SKILLS: Dict[str, List[Dict[str, Any]]] = {}
_BROWSER_EXECUTORS: Dict[str, BrowserExecutor] = {}


# ============================================================================
# 認証ヘルパー
# ============================================================================


def get_current_user_id(request: Request) -> str:
    """JWT トークンから user_id を取得"""
    # TODO: 実装時に JWT デコード処理を追加
    # 暫定: リクエストヘッダーから X-User-ID を取得（開発用）
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        user_id = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not user_id:
            raise HTTPException(status_code=401, detail="認証が必要です")
    return user_id


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
    except (TypeError, ValueError):
        return False
    return True


def _get_or_create_task_user(
    client, user_id: str, username: str = "user"
) -> Optional[str]:
    if not client or not _is_uuid(user_id):
        return None

    existing = (
        client.table("task_users")
        .select("id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]["id"]

    created = (
        client.table("task_users")
        .insert({"user_id": user_id, "username": username})
        .execute()
    )
    if created.data:
        return created.data[0]["id"]
    return None


# ============================================================================
# ユーザープロフィール エンドポイント
# ============================================================================


@router.post("/users/profile", response_model=UserProfileResponse)
async def create_user_profile(
    request_body: UserProfileRequest,
    user_id: str = Depends(get_current_user_id),
) -> UserProfileResponse:
    """ユーザープロフィール作成"""
    client = _get_supabase_client()
    task_user_id = await asyncio.to_thread(
        _get_or_create_task_user, client, user_id, request_body.username
    )
    profile_id = task_user_id or str(uuid.uuid4())
    _IN_MEMORY_PROFILES[user_id] = {
        "id": profile_id,
        "user_id": user_id,
        "username": request_body.username,
    }
    return UserProfileResponse(
        id=profile_id,
        user_id=user_id,
        username=request_body.username,
    )


@router.get("/users/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str = Depends(get_current_user_id),
) -> UserProfileResponse:
    """ユーザープロフィール取得"""
    if user_id in _IN_MEMORY_PROFILES:
        return UserProfileResponse(**_IN_MEMORY_PROFILES[user_id])
    return UserProfileResponse(
        id=str(uuid.uuid4()),
        user_id=user_id,
        username="user",
    )


# ============================================================================
# タスク実行 エンドポイント
# ============================================================================


@router.post("/tasks/execute", response_model=ExecuteTaskResponse)
async def execute_task(
    request_body: ExecuteTaskRequest,
    user_id: str = Depends(get_current_user_id),
) -> ExecuteTaskResponse:
    """
    タスク実行エンドポイント

    フロー:
    1. user_input をテキスト解析
    2. validators でセキュリティチェック
    3. 対応エンジンで実行
    4. 履歴保存（暫定: スキップ）
    5. 結果を返す
    """
    user_input = request_body.user_input.strip()

    if not user_input:
        return ExecuteTaskResponse(
            id=str(uuid.uuid4()),
            status="error",
            task_type="unknown",
            result={"message": "入力が空です"},
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    # Step 1: テキスト解析
    parsed = text_parser.parse_task_input(user_input)
    if "error" in parsed:
        return ExecuteTaskResponse(
            id=str(uuid.uuid4()),
            status="error",
            task_type="unknown",
            result={"message": parsed["error"]},
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    task_type = parsed.get("task_type", "unknown")
    action = parsed.get("action", "unknown")
    params = parsed.get("params", {})

    # Step 2: セキュリティバリデーション
    validation_result = _validate_task(task_type, action, params)
    if validation_result["status"] == "error":
        return ExecuteTaskResponse(
            id=str(uuid.uuid4()),
            status="error",
            task_type=task_type,
            result=validation_result,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    # Step 3: エンジン実行
    result = await _execute_task_engine(user_id, task_type, action, params)
    status = "success" if result.get("status") == "success" else "error"
    history_id = str(uuid.uuid4())
    created_at = _utc_now()
    await _save_history(
        user_id=user_id,
        history_id=history_id,
        task_type=task_type,
        task_input=user_input,
        executed_command=parsed,
        status=status,
        result=result,
        error_message=result.get("message") if status == "error" else None,
        created_at=created_at,
    )

    return ExecuteTaskResponse(
        id=history_id,
        status=status,
        task_type=task_type,
        result=result,
        created_at=created_at,
    )


async def _execute_task_engine(
    user_id: str, task_type: str, action: str, params: Dict[str, Any]
) -> Dict[str, Any]:
    if task_type == "file":
        executor = FileExecutor()
        if action == "create":
            return await executor.create(
                params.get("path", ""), params.get("content", "")
            )
        if action == "edit":
            return await executor.edit(
                params.get("path", ""), params.get("content", "")
            )
        if action == "delete":
            return await executor.delete(params.get("path", ""))
        if action == "read":
            return await executor.read(params.get("path", ""))

    if task_type == "cli":
        return await CLIExecutor().execute(params.get("command", ""))

    if task_type == "db":
        client = _get_supabase_client()
        return await DBExecutor(client).execute(
            params.get("query", ""), params.get("params")
        )

    if task_type == "browser":
        executor = _BROWSER_EXECUTORS.setdefault(user_id, BrowserExecutor())
        if action == "click":
            return await executor.click(params.get("selector", ""))
        if action == "input_text":
            return await executor.input_text(
                params.get("selector", ""), params.get("text")
            )
        if action == "scroll":
            return await executor.scroll(
                params.get("direction", "down"), params.get("amount", 100)
            )
        if action == "navigate":
            return await executor.navigate(params.get("url", ""))
        if action == "screenshot":
            return await executor.screenshot()
        if action == "close_session":
            return await executor.close_session()

    return {
        "status": "error",
        "action": action,
        "message": f"未サポートのタスクです: {task_type}/{action}",
    }


def _validate_task(
    task_type: str, action: str, params: Dict[str, Any]
) -> Dict[str, Any]:
    """タスク入力のセキュリティバリデーション"""

    if task_type == "file":
        path = params.get("path", "")
        is_valid, msg = validators.validate_file_operation(path, action)
        if not is_valid:
            return {"status": "error", "message": msg}

    elif task_type == "cli":
        command = params.get("command", "")
        is_valid, msg = validators.validate_cli_command(command)
        if not is_valid:
            return {"status": "error", "message": msg}

    elif task_type == "db":
        query = params.get("query", "")
        is_valid, msg = validators.validate_db_query(query, params.get("params", {}))
        if not is_valid:
            return {"status": "error", "message": msg}

    elif task_type == "browser":
        selector = params.get("selector", "")
        is_valid, msg = validators.validate_browser_selector(selector)
        if not is_valid:
            return {"status": "error", "message": msg}

    return {"status": "success"}


async def _save_history(
    user_id: str,
    history_id: str,
    task_type: str,
    task_input: str,
    executed_command: Dict[str, Any],
    status: str,
    result: Dict[str, Any],
    error_message: Optional[str],
    created_at: str,
) -> None:
    item = {
        "id": history_id,
        "task_type": task_type,
        "task_input": task_input,
        "executed_command": executed_command,
        "status": status,
        "result": result,
        "error_message": error_message,
        "created_at": created_at,
        "executed_at": created_at,
    }
    _IN_MEMORY_HISTORY.setdefault(user_id, []).insert(0, item)

    client = _get_supabase_client()
    task_user_id = await asyncio.to_thread(_get_or_create_task_user, client, user_id)
    if not client or not task_user_id:
        return

    payload = {
        "id": history_id,
        "user_id": task_user_id,
        "task_type": task_type,
        "task_input": task_input,
        "executed_command": executed_command,
        "status": status,
        "result": result,
        "error_message": error_message,
        "executed_at": created_at,
    }
    await asyncio.to_thread(
        lambda: client.table("task_history").insert(payload).execute()
    )


# ============================================================================
# タスク履歴 エンドポイント
# ============================================================================


@router.get("/tasks/history", response_model=List[TaskHistoryItem])
async def get_task_history(
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
) -> List[TaskHistoryItem]:
    """タスク実行履歴取得"""
    client = _get_supabase_client()
    task_user_id = await asyncio.to_thread(_get_or_create_task_user, client, user_id)
    if client and task_user_id:
        result = await asyncio.to_thread(
            lambda: (
                client.table("task_history")
                .select(
                    "id,task_type,task_input,status,result,error_message,created_at"
                )
                .eq("user_id", task_user_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
        )
        return [TaskHistoryItem(**row) for row in result.data]

    history = _IN_MEMORY_HISTORY.get(user_id, [])
    return [TaskHistoryItem(**row) for row in history[offset : offset + limit]]


@router.post("/tasks/history", response_model=TaskHistoryItem)
async def create_task_history(
    request_body: TaskHistoryCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> TaskHistoryItem:
    """タスク実行履歴を保存"""
    history_id = str(uuid.uuid4())
    created_at = _utc_now()
    await _save_history(
        user_id=user_id,
        history_id=history_id,
        task_type=request_body.task_type,
        task_input=request_body.task_input,
        executed_command=request_body.executed_command or {},
        status=request_body.status,
        result=request_body.result,
        error_message=request_body.error_message,
        created_at=created_at,
    )
    return TaskHistoryItem(
        id=history_id,
        task_type=request_body.task_type,
        task_input=request_body.task_input,
        status=request_body.status,
        result=request_body.result,
        error_message=request_body.error_message,
        created_at=created_at,
    )


# ============================================================================
# スキル管理 エンドポイント
# ============================================================================


@router.post("/tasks/skills", response_model=SkillResponse)
async def create_skill(
    request_body: SkillCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> SkillResponse:
    """スキル保存"""
    created_at = _utc_now()
    skill = SkillResponse(
        id=str(uuid.uuid4()),
        skill_name=request_body.skill_name,
        description=request_body.description,
        pattern=request_body.pattern.model_dump(),
        created_at=created_at,
    )
    _IN_MEMORY_SKILLS.setdefault(user_id, []).append(skill.model_dump())

    client = _get_supabase_client()
    task_user_id = await asyncio.to_thread(_get_or_create_task_user, client, user_id)
    if client and task_user_id:
        payload = {
            "id": skill.id,
            "user_id": task_user_id,
            "skill_name": skill.skill_name,
            "description": skill.description,
            "pattern": skill.pattern,
        }
        await asyncio.to_thread(
            lambda: client.table("task_skills").insert(payload).execute()
        )

    return skill


@router.get("/tasks/skills", response_model=List[SkillResponse])
async def list_skills(
    user_id: str = Depends(get_current_user_id),
) -> List[SkillResponse]:
    """スキル一覧取得"""
    client = _get_supabase_client()
    task_user_id = await asyncio.to_thread(_get_or_create_task_user, client, user_id)
    if client and task_user_id:
        result = await asyncio.to_thread(
            lambda: (
                client.table("task_skills")
                .select("id,skill_name,description,pattern,created_at")
                .eq("user_id", task_user_id)
                .order("created_at", desc=True)
                .execute()
            )
        )
        return [SkillResponse(**row) for row in result.data]
    return [SkillResponse(**skill) for skill in _IN_MEMORY_SKILLS.get(user_id, [])]


@router.delete("/tasks/skills/{skill_id}")
async def delete_skill(
    skill_id: str,
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, str]:
    """スキル削除"""
    _IN_MEMORY_SKILLS[user_id] = [
        skill for skill in _IN_MEMORY_SKILLS.get(user_id, []) if skill["id"] != skill_id
    ]
    client = _get_supabase_client()
    task_user_id = await asyncio.to_thread(_get_or_create_task_user, client, user_id)
    if client and task_user_id:
        await asyncio.to_thread(
            lambda: (
                client.table("task_skills")
                .delete()
                .eq("id", skill_id)
                .eq("user_id", task_user_id)
                .execute()
            )
        )
    return {"message": "スキル削除完了"}
