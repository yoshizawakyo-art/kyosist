---
name: codex-invoke
description: Invoke Codex CLI to execute implementation tasks. Use this whenever you need to delegate code implementation, fixes, or backend work to Codex. Covers backend APIs, database migrations, frontend code, and any other implementation tasks.
compatibility: Requires mcp__codex-cli__ask-codex tool (Codex CLI MCP server)
---

# Codex Invoke Skill

Delegate implementation work to Codex CLI with a single command.

## When to Use

Use this skill whenever you need Codex to:
- Implement backend APIs or services
- Create/execute database migrations
- Write or fix frontend code
- Perform any other code implementation or modification task

## How to Use

When you need Codex to do implementation work:

```
invoke_codex: <detailed task description>
```

Provide:
- **What** needs to be implemented/fixed
- **Why** (context and requirements)
- **Where** (relevant file paths or directories)
- **Any constraints or details** (tech stack, patterns, dependencies)

## Example

```
invoke_codex: Create authentication service in src/api/auth_service.py 
with functions for password hashing (bcrypt), JWT token generation, 
and user validation. Use Pydantic models for input validation.
Include type hints and follow FastAPI conventions.
```

## Execution

The skill will:
1. Invoke Codex CLI via `mcp__codex-cli__ask-codex` tool with `yolo=true`
2. Execute the task in the current project context
3. Return results (files created/modified, output, status)

## What Codex Returns

Codex will provide:
- Modified/created files
- Commit messages and git status
- Test results (if applicable)
- Any errors or blockers encountered

## 段階的タスク分割戦略

複雑な実装タスク（認証・DB操作・複数ファイル変更など）はトークンリミットに達する恐れがあるため、**複数の invoke_codex 呼び出しに分割して実装する**。

### いつ分割するか
- 実装ファイルが 3 つ以上になる場合
- 認証・JWT・bcrypt など複数の依存ライブラリが絡む場合
- モデル定義 → ロジック実装 → エラーハンドリングの順序依存がある場合

### 分割パターン（例: 認証エンドポイント）

**Stage 1 — モデル・スキーマ定義**

invoke_codex: Create Pydantic models for authentication in src/api/schemas/auth.py with LoginRequest (email, password) and TokenResponse (access_token, token_type).

**Stage 2 — ビジネスロジック実装**

invoke_codex: Create src/api/auth_service.py using models from Stage 1. Implement verify_password (bcrypt), create_access_token (JWT), authenticate_user.

**Stage 3 — API エンドポイント**

invoke_codex: Add POST /api/auth/login to src/api/index.py using auth_service. Return 401 on failure.

### ルール
- 各 Stage は前の Stage の成果物を参照して進める
- 1 Stage あたりの変更ファイルは 1〜2 ファイルを目安にする

## Tips

- Be specific about file paths and requirements
- Include relevant code patterns or examples if helpful
- Mention testing expectations
- Reference related files or existing code patterns to follow
