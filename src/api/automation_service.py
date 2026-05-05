"""
自立型AIエージェントMVP向けのDBサービス層。

FastAPI/Pydantic に依存せず、Supabase Client と dict を受け渡しする純粋な
ヘルパー関数を提供する。APIルートから呼び出しやすいよう、各テーブルの
CRUDと実行補助ロジックをこのモジュールに集約する。
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
from typing import Any
from urllib.parse import urlparse

from supabase import Client

ENCRYPTION_VERSION = 1
KEY_ID = "default"
NONCE_BYTES = 16
TAG_BYTES = 32
KEY_ENV_NAME = "CREDENTIAL_ENCRYPTION_KEY"

TABLE_SITES = "sites"
TABLE_CREDENTIALS = "site_credentials"
TABLE_TASKS = "automation_tasks"
TABLE_RUNS = "automation_task_runs"
TABLE_LOGS = "automation_run_logs"
TABLE_GENERATED_FILES = "generated_files"


# ── 共通DBヘルパー ──────────────────────────────────────────────


def _first_or_none(data: list[dict] | None) -> dict | None:
    return data[0] if data else None


def _insert(client: Client, table: str, data: dict) -> dict:
    result = client.table(table).insert(data).execute()
    if not result.data:
        raise RuntimeError(f"{table} の作成に失敗しました")
    return result.data[0]


def _select_by_id(client: Client, table: str, record_id: str) -> dict | None:
    result = client.table(table).select("*").eq("id", record_id).limit(1).execute()
    return _first_or_none(result.data)


def _list(
    client: Client,
    table: str,
    *,
    filters: dict[str, Any] | None = None,
    order_by: str = "created_at",
    desc: bool = True,
    limit: int | None = None,
) -> list[dict]:
    query = client.table(table).select("*")
    for key, value in (filters or {}).items():
        if value is not None:
            query = query.eq(key, value)
    query = query.order(order_by, desc=desc)
    if limit is not None:
        query = query.limit(limit)
    result = query.execute()
    return result.data


def _update(client: Client, table: str, record_id: str, data: dict) -> dict:
    result = client.table(table).update(data).eq("id", record_id).execute()
    if not result.data:
        raise RuntimeError(f"{table} の更新に失敗しました")
    return result.data[0]


def _delete(client: Client, table: str, record_id: str) -> None:
    client.table(table).delete().eq("id", record_id).execute()


# ── 認証情報の暗号化 ────────────────────────────────────────────


def _credential_key() -> bytes:
    key = os.environ.get(KEY_ENV_NAME)
    if not key:
        raise RuntimeError(f"{KEY_ENV_NAME} が設定されていません")
    return hashlib.sha256(key.encode("utf-8")).digest()


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    blocks = []
    counter = 0
    while sum(len(block) for block in blocks) < length:
        counter_bytes = counter.to_bytes(8, "big")
        blocks.append(hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest())
        counter += 1
    return b"".join(blocks)[:length]


def encrypt_secret(secret: str) -> dict:
    """
    認証情報を標準ライブラリのみで暗号化する。

    `CREDENTIAL_ENCRYPTION_KEY` は必須。返却値は `encrypted_secret` と
    `encryption_version` をDBへ保存できる dict。

    注意:
      この実装は cryptography 未導入環境でもMVPを動かすための簡易実装であり、
      認証付き暗号(AES-GCM/ChaCha20-Poly1305等)の代替として本番利用しないこと。
      本番では `cryptography` などの検証済みライブラリへ移行する。
    """
    key = _credential_key()
    nonce = secrets.token_bytes(NONCE_BYTES)
    plaintext = secret.encode("utf-8")
    stream = _keystream(key, nonce, len(plaintext))
    ciphertext = bytes(a ^ b for a, b in zip(plaintext, stream))
    tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    payload = base64.urlsafe_b64encode(tag + ciphertext).decode("ascii")
    return {
        "encrypted_secret": payload,
        "encryption_version": ENCRYPTION_VERSION,
        "key_id": KEY_ID,
        "encryption_nonce": base64.urlsafe_b64encode(nonce).decode("ascii"),
    }


def decrypt_secret(
    encrypted_secret: str,
    encryption_version: int,
    encryption_nonce: str,
) -> str:
    """
    `encrypt_secret()` の保存値を復号する。

    `CREDENTIAL_ENCRYPTION_KEY` は必須。この簡易実装はMVP用であり、
    本番相当の暗号強度を保証しない。
    """
    if encryption_version != ENCRYPTION_VERSION:
        raise ValueError(f"未対応の暗号化バージョンです: {encryption_version}")

    key = _credential_key()
    raw = base64.urlsafe_b64decode(encrypted_secret.encode("ascii"))
    nonce = base64.urlsafe_b64decode(encryption_nonce.encode("ascii"))
    if len(nonce) != NONCE_BYTES or len(raw) < TAG_BYTES:
        raise ValueError("暗号文の形式が不正です")

    tag = raw[:TAG_BYTES]
    ciphertext = raw[TAG_BYTES:]
    expected = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("認証情報の検証に失敗しました")

    stream = _keystream(key, nonce, len(ciphertext))
    plaintext = bytes(a ^ b for a, b in zip(ciphertext, stream))
    return plaintext.decode("utf-8")


# ── sites CRUD ─────────────────────────────────────────────────


def create_site(client: Client, data: dict) -> dict:
    return _insert(client, TABLE_SITES, data)


def list_sites(client: Client, filters: dict[str, Any] | None = None) -> list[dict]:
    return _list(client, TABLE_SITES, filters=filters)


def get_site(client: Client, site_id: str) -> dict | None:
    return _select_by_id(client, TABLE_SITES, site_id)


def update_site(client: Client, site_id: str, data: dict) -> dict:
    return _update(client, TABLE_SITES, site_id, data)


def delete_site(client: Client, site_id: str) -> None:
    _delete(client, TABLE_SITES, site_id)


# ── credentials CRUD ────────────────────────────────────────────


def create_credential(client: Client, data: dict, secret: str) -> dict:
    record = data | encrypt_secret(secret)
    return _insert(client, TABLE_CREDENTIALS, record)


def list_credentials(
    client: Client, filters: dict[str, Any] | None = None
) -> list[dict]:
    return _list(client, TABLE_CREDENTIALS, filters=filters)


def get_credential(client: Client, credential_id: str) -> dict | None:
    return _select_by_id(client, TABLE_CREDENTIALS, credential_id)


def update_credential(
    client: Client, credential_id: str, data: dict, secret: str | None = None
) -> dict:
    record = dict(data)
    if secret is not None:
        record.update(encrypt_secret(secret))
    return _update(client, TABLE_CREDENTIALS, credential_id, record)


def delete_credential(client: Client, credential_id: str) -> None:
    _delete(client, TABLE_CREDENTIALS, credential_id)


def get_decrypted_credential_secret(client: Client, credential_id: str) -> str | None:
    credential = get_credential(client, credential_id)
    if not credential:
        return None
    return decrypt_secret(
        credential["encrypted_secret"],
        credential["encryption_version"],
        credential["encryption_nonce"],
    )


# ── tasks CRUD ─────────────────────────────────────────────────


def create_task(client: Client, data: dict) -> dict:
    return _insert(client, TABLE_TASKS, data)


def list_tasks(client: Client, filters: dict[str, Any] | None = None) -> list[dict]:
    return _list(client, TABLE_TASKS, filters=filters)


def get_task(client: Client, task_id: str) -> dict | None:
    return _select_by_id(client, TABLE_TASKS, task_id)


def update_task(client: Client, task_id: str, data: dict) -> dict:
    return _update(client, TABLE_TASKS, task_id, data)


def delete_task(client: Client, task_id: str) -> None:
    _delete(client, TABLE_TASKS, task_id)


# ── runs CRUD / 補助 ───────────────────────────────────────────


def create_run(client: Client, data: dict) -> dict:
    return _insert(client, TABLE_RUNS, data)


def list_runs(client: Client, filters: dict[str, Any] | None = None) -> list[dict]:
    return _list(client, TABLE_RUNS, filters=filters, order_by="started_at")


def get_run(client: Client, run_id: str) -> dict | None:
    return _select_by_id(client, TABLE_RUNS, run_id)


def update_run(client: Client, run_id: str, data: dict) -> dict:
    return _update(client, TABLE_RUNS, run_id, data)


def delete_run(client: Client, run_id: str) -> None:
    _delete(client, TABLE_RUNS, run_id)


def update_run_status(
    client: Client,
    run_id: str,
    status: str,
    *,
    current_step_id: str | None = None,
    resume_state_json: dict | None = None,
    output_file_path: str | None = None,
    finished_at: str | None = None,
) -> dict:
    data: dict[str, Any] = {"status": status}
    optional_values = {
        "current_step_id": current_step_id,
        "resume_state_json": resume_state_json,
        "output_file_path": output_file_path,
        "finished_at": finished_at,
    }
    data.update(
        {key: value for key, value in optional_values.items() if value is not None}
    )
    return update_run(client, run_id, data)


# ── logs CRUD / 補助 ───────────────────────────────────────────


def create_log(client: Client, data: dict) -> dict:
    return _insert(client, TABLE_LOGS, data)


def list_logs(client: Client, filters: dict[str, Any] | None = None) -> list[dict]:
    return _list(client, TABLE_LOGS, filters=filters, order_by="created_at", desc=False)


def get_log(client: Client, log_id: str) -> dict | None:
    return _select_by_id(client, TABLE_LOGS, log_id)


def update_log(client: Client, log_id: str, data: dict) -> dict:
    return _update(client, TABLE_LOGS, log_id, data)


def delete_log(client: Client, log_id: str) -> None:
    _delete(client, TABLE_LOGS, log_id)


def append_run_log(
    client: Client,
    run_id: str,
    level: str,
    message: str,
    details_json: dict | None = None,
) -> dict:
    return create_log(
        client,
        {
            "run_id": run_id,
            "level": level,
            "message": message,
            "details_json": details_json or {},
        },
    )


# ── generated_files CRUD / 補助 ─────────────────────────────────


def create_generated_file(client: Client, data: dict) -> dict:
    return _insert(client, TABLE_GENERATED_FILES, data)


def list_generated_files(
    client: Client, filters: dict[str, Any] | None = None
) -> list[dict]:
    return _list(client, TABLE_GENERATED_FILES, filters=filters)


def get_generated_file(client: Client, generated_file_id: str) -> dict | None:
    return _select_by_id(client, TABLE_GENERATED_FILES, generated_file_id)


def update_generated_file(client: Client, generated_file_id: str, data: dict) -> dict:
    return _update(client, TABLE_GENERATED_FILES, generated_file_id, data)


def delete_generated_file(client: Client, generated_file_id: str) -> None:
    _delete(client, TABLE_GENERATED_FILES, generated_file_id)


def find_generated_file_for_month(
    client: Client, task_id: str, target_month: str
) -> dict | None:
    result = (
        client.table(TABLE_GENERATED_FILES)
        .select("*")
        .eq("task_id", task_id)
        .eq("target_month", target_month)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return _first_or_none(result.data)


def has_generated_file_for_month(
    client: Client, task_id: str, target_month: str
) -> bool:
    return find_generated_file_for_month(client, task_id, target_month) is not None


# ── 禁止サイト判定 ──────────────────────────────────────────────


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return [stripped]
        return parsed if isinstance(parsed, list) else [parsed]
    return [value]


def _candidate_domain(value: str) -> str:
    candidate = value.strip().lower()
    if not candidate:
        return ""
    parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
    return (parsed.hostname or candidate).removeprefix("www.")


def _domain_matches(candidate: str, rule: str) -> bool:
    candidate_domain = _candidate_domain(candidate)
    rule_domain = _candidate_domain(rule)
    return candidate_domain == rule_domain or candidate_domain.endswith(
        f".{rule_domain}"
    )


def _text_matches(candidate: str, rule: str) -> bool:
    candidate_text = candidate.strip().lower()
    rule_text = rule.strip().lower()
    return bool(rule_text) and rule_text in candidate_text


def _rule_values(rule: Any) -> list[str]:
    if isinstance(rule, dict):
        values = []
        for key in ("name", "site_name", "domain", "url", "pattern", "value"):
            value = rule.get(key)
            if value:
                values.append(str(value))
        return values
    return [str(rule)]


def is_site_blocked(
    candidates: list[str],
    *,
    task: dict | None = None,
    site: dict | None = None,
) -> dict:
    """
    サイト名/ドメイン候補がタスク設定またはサイト定義でブロックされるか判定する。

    判定順:
      1. `task["blocked_site_rules"]` の文字列/JSON配列/dict配列に一致したらブロック。
      2. `site["blocked_site_rules"]` に一致したらブロック。
      3. `site["allowed_domains"]` が設定済みで、候補ドメインがどれにも一致しなければブロック。

    戻り値:
      {"blocked": bool, "reason": str, "matched_rule": Any | None}
    """
    normalized_candidates = [candidate for candidate in candidates if candidate.strip()]
    task = task or {}
    site = site or {}

    for rule in _as_list(task.get("blocked_site_rules")):
        for value in _rule_values(rule):
            if any(
                _domain_matches(candidate, value) or _text_matches(candidate, value)
                for candidate in normalized_candidates
            ):
                return {
                    "blocked": True,
                    "reason": "task.blocked_site_rules に一致しました",
                    "matched_rule": rule,
                }

    for pattern in _as_list(site.get("blocked_site_rules")):
        pattern_text = str(pattern)
        if any(
            _domain_matches(candidate, pattern_text)
            or _text_matches(candidate, pattern_text)
            for candidate in normalized_candidates
        ):
            return {
                "blocked": True,
                "reason": "site.blocked_site_rules に一致しました",
                "matched_rule": pattern,
            }

    allowed_domains = [str(domain) for domain in _as_list(site.get("allowed_domains"))]
    domain_candidates = [
        candidate
        for candidate in normalized_candidates
        if "." in _candidate_domain(candidate)
    ]
    if allowed_domains and domain_candidates:
        allowed = any(
            _domain_matches(candidate, allowed_domain)
            for candidate in domain_candidates
            for allowed_domain in allowed_domains
        )
        if not allowed:
            return {
                "blocked": True,
                "reason": "site.allowed_domains の範囲外です",
                "matched_rule": allowed_domains,
            }

    return {"blocked": False, "reason": "", "matched_rule": None}
