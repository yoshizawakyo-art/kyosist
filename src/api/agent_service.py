"""
ReAct (Thought/Action/Observation) 自律エージェントサービス。

Groq (Llama 3.3 70B) を推論エンジンとして使用し、以下のツールを呼び出す:
  - web_search  : Tavily API でウェブ検索
  - notion_write: Notion API でデータベースに書き込み

各ステップは Supabase の agent_steps テーブルに永続化される。
Groq のレート制限には指数バックオフで対応する。
"""

import ast
import asyncio
import json
import logging
import os
import random
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Optional

import httpx
from groq import AsyncGroq
from supabase import Client

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10
MAX_SEARCH_RESULTS = 5
GROQ_MAX_RETRIES = 5
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """\
あなたは自律的なAIリサーチアシスタントです。ユーザーのリクエストを達成するために
利用可能なツールを使って段階的に考え行動します。

利用可能なツール:
- web_search(query) : 指定クエリでウェブを検索し最新情報を取得する
- notion_write(title, items) : Notionデータベースに研究結果を保存する（itemsはPythonリスト形式）

必ず以下のフォーマットで応答してください:

Thought: <現状を分析して次のアクションを計画する>
Action: tool_name(arguments)

または全ての作業が完了したら:
Final Answer: <ユーザーへの最終的な回答>

重要なルール:
- 必ず上記フォーマットを厳守する
- 1回の応答にはThought+ActionかFinal Answerのどちらかのみを含める
- 最新AIニュースの場合: 英語と日本語で複数回検索して幅広く情報収集する
- 収集した情報をNotionに書き込む際は各項目に日付・タイトル・概要・URLを含める
- Notionへの書き込みは研究が完了した後に必ず実行する
- 登録済みカスタムスキルが利用可能な場合は、適切なタイミングで skill_call を使う
"""


def _build_system_prompt(skills: list[dict]) -> str:
    """スキル一覧を含む動的なシステムプロンプトを生成する。"""
    if not skills:
        return SYSTEM_PROMPT
    skill_lines = "\n".join(
        f'- skill_call("{s["name"]}", input): {s["description"]}' for s in skills
    )
    return SYSTEM_PROMPT + f"\n\n登録済みカスタムスキル:\n{skill_lines}"


# ── データ構造 ──────────────────────────────────────────────────


@dataclass
class AgentStep:
    step_type: str  # "thought" | "action" | "observation" | "answer"
    content: str
    step_index: int
    tool_name: Optional[str] = None


# ── ツール実装 ──────────────────────────────────────────────────


async def web_search(query: str) -> str:
    """Tavily API でウェブ検索を実行する。"""
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return "エラー: TAVILY_API_KEY が設定されていません"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": MAX_SEARCH_RESULTS,
                    "search_depth": "advanced",
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            return (
                f"検索エラー (HTTP {e.response.status_code}): {e.response.text[:300]}"
            )
        except httpx.RequestError as e:
            return f"ネットワークエラー: {e}"

    data = response.json()
    results = data.get("results", [])
    if not results:
        return "検索結果が見つかりませんでした"

    lines = []
    for i, item in enumerate(results, 1):
        lines.append(
            f"{i}. {item.get('title', '(タイトルなし)')}\n"
            f"   URL: {item.get('url', '')}\n"
            f"   {item.get('content', '')[:400]}"
        )
    return "\n\n".join(lines)


async def notion_write(title: str, items: list) -> str:
    """Notion データベースにページを作成し、箇条書きで項目を書き込む。"""
    token = os.environ.get("NOTION_API_KEY", "")
    database_id = os.environ.get("NOTION_DATABASE_ID", "")

    if not token or not database_id:
        return "エラー: NOTION_API_KEY または NOTION_DATABASE_ID が設定されていません"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    children = [
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": str(item)[:2000]}}]
            },
        }
        for item in items
    ]

    payload = {
        "parent": {"database_id": database_id},
        "properties": {"名前": {"title": [{"text": {"content": str(title)[:100]}}]}},
        "children": children,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "https://api.notion.com/v1/pages",
                json=payload,
                headers=headers,
            )
        except httpx.RequestError as e:
            return f"Notion ネットワークエラー: {e}"

    if response.status_code == 200:
        return f"Notion への書き込みが完了しました: 「{title}」({len(items)} 件)"
    error_msg = response.json().get("message", response.text[:300])
    return f"Notion エラー (HTTP {response.status_code}): {error_msg}"


async def skill_call(skill_name: str, input_text: str, skills: list[dict]) -> str:
    """登録済みスキルをWebhookで呼び出す。"""
    skill = next((s for s in skills if s["name"] == skill_name), None)
    if not skill:
        return f"スキルが見つかりません: {skill_name}"

    method = skill.get("action_method", "POST").upper()
    url = skill["action_url"]
    body_template = skill.get("action_body_template", "")

    if body_template:
        body = body_template.replace("{input}", input_text)
    else:
        body = json.dumps({"input": input_text}, ensure_ascii=False)

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        try:
            if method == "GET":
                response = await http_client.get(url, params={"input": input_text})
            else:
                response = await http_client.post(
                    url,
                    content=body,
                    headers={"Content-Type": "application/json"},
                )
            return f"スキル「{skill_name}」の実行結果 (HTTP {response.status_code}): {response.text[:500]}"
        except httpx.RequestError as e:
            return f"スキル「{skill_name}」の実行エラー: {e}"


# ── Groq 呼び出し ───────────────────────────────────────────────


async def _call_groq_with_retry(groq_client: AsyncGroq, prompt: str) -> str:
    """指数バックオフ付きで Groq API を呼び出す。"""
    for attempt in range(GROQ_MAX_RETRIES):
        try:
            response = await groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            err_str = str(exc).lower()
            is_retriable = any(
                kw in err_str for kw in ("429", "rate", "quota", "resource exhausted")
            )
            if is_retriable and attempt < GROQ_MAX_RETRIES - 1:
                wait = (2**attempt) + random.uniform(0, 1)
                logger.warning(
                    "Groq レート制限: %.1f 秒待機 (試行 %d/%d)",
                    wait,
                    attempt + 1,
                    GROQ_MAX_RETRIES,
                )
                await asyncio.sleep(wait)
                continue
            raise
    raise RuntimeError("Groq API: 最大リトライ数に達しました")


# ── ReAct パーサー ──────────────────────────────────────────────


def _parse_thought(text: str) -> Optional[str]:
    m = re.search(
        r"^Thought:\s*(.+?)(?=^Action:|^Final Answer:|$)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return m.group(1).strip() if m else None


def _parse_action(text: str) -> Optional[str]:
    m = re.search(
        r"^Action:\s*(.+?)(?=^(?:Thought|Final Answer|Observation):|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return m.group(1).strip() if m else None


def _parse_final_answer(text: str) -> Optional[str]:
    m = re.search(r"^Final Answer:\s*(.+)$", text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else None


async def _execute_action(action_text: str, skills: list[dict]) -> tuple[str, str]:
    """アクション文字列を解析してツールを実行する。(tool_name, observation) を返す。"""
    m = re.match(r"^(\w+)\((.*)\)$", action_text.strip(), re.DOTALL)
    if not m:
        return "unknown", f"アクションを解析できませんでした: {action_text}"

    tool_name = m.group(1)
    args_str = m.group(2).strip()

    try:
        args = ast.literal_eval(f"({args_str},)")
    except Exception as exc:
        return tool_name, f"引数の解析エラー: {exc}"

    if tool_name == "web_search":
        if not args:
            return tool_name, "クエリが指定されていません"
        return tool_name, await web_search(str(args[0]))

    if tool_name == "notion_write":
        if len(args) < 2:
            return tool_name, "タイトルと項目リストが必要です"
        items = list(args[1]) if isinstance(args[1], (list, tuple)) else [str(args[1])]
        return tool_name, await notion_write(str(args[0]), items)

    if tool_name == "skill_call":
        if len(args) < 2:
            return tool_name, "スキル名と入力テキストが必要です"
        return tool_name, await skill_call(str(args[0]), str(args[1]), skills)

    return tool_name, f"未知のツール: {tool_name}"


# ── Supabase 永続化 ─────────────────────────────────────────────


def _save_step(client: Client, message_id: str, step: AgentStep) -> None:
    """エージェントステップを agent_steps テーブルに保存する（同期）。"""
    record = {
        "message_id": message_id,
        "step_index": step.step_index,
        "step_type": step.step_type,
        "content": step.content,
    }
    if step.tool_name:
        record["tool_name"] = step.tool_name
    client.table("agent_steps").insert(record).execute()


# ── メインエージェントループ ────────────────────────────────────


async def run_agent(
    user_message: str,
    groq_client: AsyncGroq,
    supabase_client: Client,
    message_id: str,
    skills: list[dict] | None = None,
) -> AsyncGenerator[AgentStep, None]:
    """
    ReAct ループを実行し、各ステップを AsyncGenerator で yield する。
    同時に Supabase の agent_steps テーブルにも永続化する。
    """
    skills = skills or []
    history: list[str] = [f"User: {user_message}"]
    step_index = 0

    for _iteration in range(MAX_ITERATIONS):
        prompt = _build_system_prompt(skills) + "\n\n" + "\n".join(history)

        try:
            llm_output = await _call_groq_with_retry(groq_client, prompt)
        except Exception as exc:
            error_step = AgentStep(
                step_type="observation",
                content=f"LLM エラー: {exc}",
                step_index=step_index,
            )
            await asyncio.to_thread(_save_step, supabase_client, message_id, error_step)
            yield error_step
            return

        thought = _parse_thought(llm_output)
        action = _parse_action(llm_output)
        final_answer = _parse_final_answer(llm_output)

        if thought:
            thought_step = AgentStep(
                step_type="thought", content=thought, step_index=step_index
            )
            step_index += 1
            await asyncio.to_thread(
                _save_step, supabase_client, message_id, thought_step
            )
            yield thought_step

        if final_answer:
            answer_step = AgentStep(
                step_type="answer", content=final_answer, step_index=step_index
            )
            await asyncio.to_thread(
                _save_step, supabase_client, message_id, answer_step
            )
            yield answer_step
            return

        if action:
            action_step = AgentStep(
                step_type="action", content=action, step_index=step_index
            )
            step_index += 1
            await asyncio.to_thread(
                _save_step, supabase_client, message_id, action_step
            )
            yield action_step

            tool_name, observation = await _execute_action(action, skills)

            obs_step = AgentStep(
                step_type="observation",
                content=observation[:2000],
                step_index=step_index,
                tool_name=tool_name,
            )
            step_index += 1
            await asyncio.to_thread(_save_step, supabase_client, message_id, obs_step)
            yield obs_step

            history.append(f"Thought: {thought or ''}")
            history.append(f"Action: {action}")
            history.append(f"Observation: {observation[:800]}")
        else:
            # LLM がフォーマットに従わなかった場合は誘導する
            history.append(llm_output)
            history.append("Action または Final Answer を必ず含めてください。")

    timeout_step = AgentStep(
        step_type="answer",
        content="最大反復回数に達しました。現時点の情報をもとに処理を完了します。",
        step_index=step_index,
    )
    await asyncio.to_thread(_save_step, supabase_client, message_id, timeout_step)
    yield timeout_step


def build_agent_event(step: AgentStep, conversation_id: str) -> str:
    """SSE 用のイベント文字列を生成する。"""
    payload = {
        "type": step.step_type,
        "content": step.content,
        "step_index": step.step_index,
        "conversation_id": conversation_id,
    }
    if step.tool_name:
        payload["tool_name"] = step.tool_name
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
