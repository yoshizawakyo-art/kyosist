# ペンディングタスク一覧

最終更新: 2026-05-06

---

## ✅ 完了済み

### codex-invoke スキル最適化（iteration-2）
- [x] 段階的タスク分割戦略を SKILL.md に追記
- [x] evals.json に staged テストケース（id=4,5,6）追加
- [x] iteration-2 ベンチマーク実行 → 100% pass rate 達成（iteration-1 は 60%）
- [x] Path A（iteration-2 で最適化して本番投入）を採用・完了

### 認証基盤ファイル実装（マージ済み）
- [x] `src/api/schemas/auth.py` — LoginRequest（EmailStr + min_length=8）/ TokenResponse / LoginResponse / AuthUserResponse / LogoutResponse
- [x] `src/api/schemas/__init__.py`
- [x] `src/api/auth_service.py` — hash_password / verify_password (bcrypt) / create_access_token・verify_token (PyJWT) / authenticate_user

### PDCAワークフロー整備
- [x] `pdca-check-reviewer` エージェント作成（model: opus, color: red, CHECK OK/NG 専用）
- [x] `.claude/rules/pdca-workflow.md` — Phase 3 Check に pdca-check-reviewer 必須使用を明記
- [x] `.claude/rules/subagent-selection.md` — pdca-check-reviewer 追加
- [x] `CLAUDE.md` — Check 担当を pdca-check-reviewer に変更
- [x] `.claude/rules/error-recovery.md` — 新規作成（エラー発生時のルール更新プロトコル）

### PR #4 マージ完了
- [x] PR #4 `feat: 認証API統合とPDCAワークフロー整備` を作成・更新
- [x] Codex 仕様で PDCA Check / PR 最終レビューを実施
- [x] Vercel / Vercel Preview Comments の成功を確認
- [x] squash merge 完了（merge commit: `4f4c3c8610a6b7201d3ccce448df8b9aaaa3b085`）
- [x] リモートブランチ `fix/main-js-import-not-loaded` を削除

### Task Ledger 更新漏れ防止ルール最適化
- [x] `AGENTS.md` に `.claude/doc/pending-tasks.md` 更新必須ルールを追加
- [x] `CLAUDE.md` に Task Ledger 更新ゲートを追加
- [x] `.claude/rules/pdca-workflow.md` のフロー / Definition of Done / 禁止事項に pending-tasks 更新を追加
- [x] `rule-optimization` skill を `~/.codex/skills/rule-optimization` に作成
- [x] `rule-optimization` skill validation 通過
- [x] skill / rule 更新時に `.claude` 配下の対応ファイルも同期確認・更新するルールを追加
- [x] `.claude/skills/rule-optimization/SKILL.md` を追加し、Codex 側 skill と整合
- [x] rule / skill 更新検知 hook `.claude/hooks/rule-skill-sync-reminder.ps1` を追加
- [x] `.claude/settings.local.json` の `PostToolUse` に rule / skill 同期リマインダー hook を登録
- [x] `rule-optimization` skill に hook 登録手順と検証手順を追記
- [x] hook script を `powershell.exe` で代表入力テストし、リマインダー出力を確認
- [x] クレジット残量 5% 未満検知 hook `.claude/hooks/credit-handoff-generator.ps1` を追加
- [x] `.claude/settings.local.json` の `Stop` / `UserPromptSubmit` に引継ぎ Markdown 生成 hook を登録
- [x] `rule-optimization` skill に session handoff hook パターンを追記
- [x] 4.9% 代表 payload で `.claude/doc/session-handoffs/session-handoff-*.md` 生成を確認
- [x] 15% 代表 payload で no-op を確認
- [x] PowerShell 5.1 実行時の文字化けを避けるため、handoff hook の UTF-8 入出力を明示

---

## 🔲 未完了・引き継ぎ事項

### ローカル作業ツリー上の未処理

未コミット変更あり:
- `.agents/`, `.codex/` 配下の大量削除差分（PR #4 には含めず保留）
- `.claude/agents/pdca-check-reviewer.md` のローカル差分（PR #4 には含めず保留）
- `src/ARCHITECTURE.md` / `src/CODING_GUIDE.md` / `src/README.md` / `src/public/chat/main_new.js` の CRLF 系差分（PR #4 には含めず保留）
- `.agents/AGENTS.md`（未追跡・要確認）

### 認証機能実装（メイン実装フェーズ）

#### フェーズ 1: バックエンド認証基盤

**Task 1-1: DB マイグレーション**
- [x] 005_authentication.sql / 006_sessions.sql を確認
- [x] 既存 DB スキーマと migration history の不整合を修復（001〜006 applied）
- [x] `supabase db push --dry-run` で `Remote database is up to date.` を確認
- 参照: `supabase/migrations/`

**Task 1-2: 認証エンドポイント**
- [x] FastAPI エンドポイント: `POST /api/auth/login` を `src/api/index.py` に追加
  - auth_service.py / schemas/auth.py はすでに実装済み → 統合するだけ
  - HTTPException 401 on failure / response_model=LoginResponse
- [x] エラーハンドリング（401/500）

**Task 1-3 〜 1-6**
- [x] JWT 認証 dependency 実装（Bearer token 検証 + セッション照合）
- [x] ユーザーセッション管理（ログイン時作成、認証時 last_seen_at 更新）
- [x] トークンリフレッシュ（`POST /api/auth/refresh`）
- [x] ログアウト処理（`POST /api/auth/logout`）
- [x] ログイン中ユーザー取得（`GET /api/auth/me`）

#### フェーズ 2: フロントエンド認証 UI

- [x] ログインフォーム（`src/public/auth/login.html`）
- [x] フォームバリデーション
- [x] `/api/auth/login` との API 統合
- [x] JWT トークン localStorage 管理
- [x] エラー表示

#### フェーズ 3: Codex 継続確認（2026-05-04）

- [x] `auth_service.py` の未導入依存（python-jose / passlib）を、`requirements.txt` と一致する PyJWT / bcrypt に修正
- [x] `schemas/auth.py` を実APIレスポンス（LoginResponse / AuthUserResponse / LogoutResponse）に合わせて拡張
- [x] `run.py` の import を維持したまま改行コード差分を整理
- [x] `python3 -m py_compile run.py src/api/index.py src/api/auth_service.py src/api/schemas/auth.py`
- [x] JWT 秘密鍵のハードコード fallback を廃止
- [x] CORS wildcard を廃止し、`CORS_ALLOW_ORIGINS` による設定へ変更
- [x] PR #4 に同一ブランチ push し、マージ完了
- [x] `ruff check .`
- [x] `ruff format --check .`
- [x] FastAPI import / ローカル起動確認（`uvicorn run:app`、`/` と `/api/conversations` が HTTP 200）
- [x] Ruff 指摘対応: `run.py` の `noqa` 整合、`skills/codex-skill-creator` の未使用変数削除、format、lambda 排除

---

## 実装方針（確定）

- 実装は `codex exec --dangerously-bypass-approvals-and-sandbox` 経由で Codex に移譲
  - `mcp__codex-cli__ask-codex` は `--full-auto` エラーが出るため Bash 直接実行
- Do → Check（`pdca-check-reviewer`）→ PR作成 → PR最終レビュー → マージ のワークフロー
- 複雑な実装（複数ファイル・多依存）は Stage 分割で token limit を回避
- Task 1-2 は schemas/auth_service が完成済みなので Stage 1個（endpoint のみ）で完結する見込み

---

## Completed Updates 2026-05-04
- [x] Recreated `.claude/agents/pdca-check-reviewer.md` with the exact requested PDCA Check reviewer content.
- [x] Completed previously blocked Ruff and FastAPI local verification using Windows Python / PowerShell.

## Completed Updates 2026-05-06
- [x] Created `supabase/migrations/007_conversations_user_id.sql` for conversation user isolation.
- [x] Completed Stage 1 chat backend auth/streaming update: `/api/chat` now uses authenticated Groq SSE streaming with conversation history, conversation endpoints are JWT-guarded, conversation rows are scoped by `user_id`, and `ruff check .` / `ruff format --check .` pass.

---

## Completed Updates 2026-05-06
- [x] Created commit `b7f4f3d` for Task Ledger completion rule updates in `CLAUDE.md`, `AGENTS.md`, and synchronized `.claude/rules/` files.
- [x] Created commit `2625668` for `automation_service` indentation, `run.py` noqa, and `src/api/index.py` formatting updates.
- [x] Created commit `b18968b` for `.agents/.codex` cleanup, `skills/` script updates, and `.claude/agents/pdca-check-reviewer.md` local changes.
- [x] Verified Python changes with `ruff check .` and `ruff format --check .` before committing.
- [x] Pushed branch `fix/main-js-import-not-loaded` and created PR #7: https://github.com/yoshizawakyo-art/kyosist/pull/7. Requested PR #5 could not be assigned because GitHub auto-numbered the new PR as #7.
- [x] Updated PR #7 body to include all `.claude/rules/` changes（pdca-workflow.md / subagent-selection.md）.
- [x] Executed Check phase（pdca-check-reviewer.md ガイドラインに準拠）→ CHECK OK.
- [x] Executed PR Final Review（pdca-check-reviewer.md ガイドライン）→ PR REVIEW OK.
- [x] Merged PR #7 to main（merge commit）: https://github.com/yoshizawakyo-art/kyosist/pull/7.
  - **Note**: Merge conflict with `main` branch required resolution. Adopted `main` version for `.claude/` rule files to preserve concurrent updates. PR #7 changes to rule files are included but may require verification that all intended updates are present.
- [x] Verified and restored PR #7 lost ルール強化:
  - CLAUDE.md: Task Ledger更新必須・ルール / Skill 整合性必須ルールを復元
  - .claude/rules/pdca-workflow.md: Task Ledger 更新条件セクションを復元
  - push: `fix: PR #7 マージ時のコンフリクト解決で失われたルール強化を復元`
- [x] Holding branch `fix/main-js-import-not-loaded` remains; リモートプッシュのみ（削除なし）.
- [x] Stage 1 DB migration/backend implementation completed: added `supabase/migrations/007_conversations_user_id.sql`, scoped conversations by authenticated user, added JWT guards to conversation endpoints, and replaced `POST /api/chat` with Groq-backed SSE streaming. Verification: `ruff check src/api/index.py`, `ruff format --check src/api/index.py`, `python -m py_compile src/api/index.py`.

---

## Completed Updates 2026-05-06 (Task 3 実装)
- [x] Completed Task 3 chat frontend implementation: added `kyosist_token` Authorization headers to chat frontend fetch calls, changed `/api/chat` handling to SSE streaming via `response.body.getReader()`, added 401 redirect to `/auth/login.html`, and added Authorization to sidebar `/api/conversations` fetch.
- [x] Verified Task 3 with `ruff check .`, `ruff format --check .`, and UTF-8 ES module syntax checks for `src/public/chat/main.js` / `src/public/common/kyouCommon.js`.
- [x] Executed Playwright tests: 6/6 PASS ✅

## Completed Updates 2026-05-06 (Rule Optimization)
- [x] Added a mandatory post-work progress update rule: after any work changes files, verification status, task status, blockers, or next steps, update `.claude/doc/pending-tasks.md` before the final response, including rule/documentation-only changes.
- [x] Updated Codex-facing rules: `AGENTS.md` and `.agents/AGENTS.md`.
- [x] Updated Claude-side counterparts: `CLAUDE.md`, `.claude/rules/pdca-workflow.md`, and `.agents/claude/.claude/rules/pdca-workflow.md`.
- [x] No hook changes were needed; the rule is a completion gate, not an automation request.

## Completed Updates 2026-05-06 (Harness Skill)
- [x] Created Codex-side `harness` skill at `/home/yoshizawa/.codex/skills/harness/SKILL.md` based on the supplied harness engineering brief.
- [x] Added `agents/openai.yaml` metadata for the Codex `harness` skill.
- [x] Updated Claude-side counterpart `.claude/skills/harness/SKILL.md` so Codex/Claude harness workflows stay behaviorally aligned.
- [x] Validation: `python3 /home/yoshizawa/.codex/skills/.system/skill-creator/scripts/quick_validate.py /home/yoshizawa/.codex/skills/harness` → PASS.
- [x] Validation: parsed `/home/yoshizawa/.codex/skills/harness/agents/openai.yaml` with PyYAML → PASS.
- [x] Validation: `git diff --check -- .claude/skills/harness/SKILL.md .claude/doc/pending-tasks.md` → PASS.

## Completed Updates 2026-05-06 (Harness Slash Command)
- [x] Synced `.agents/skills/harness/SKILL.md` with the current Claude/Codex harness optimization workflow and added command-awareness to the harness surface.
- [x] Updated `/home/yoshizawa/.codex/skills/harness/SKILL.md` and `.claude/skills/harness/SKILL.md` to inspect `.agents/rules`, `.agents/skills`, `.agents/commands`, and `.agents/settings*.json` instead of the nonexistent `.agents/claude/.claude` path.
- [x] Added `/harness` slash command entry points: `.claude/commands/harness.md` and `.agents/commands/harness.md`.
- [x] Updated `AGENTS.md`, `CLAUDE.md`, and `.agents/AGENTS.md` so rule / skill / hook / slash-command synchronization points to the actual `.claude/` + `.agents/` layout.
- [x] Validation: `quick_validate.py` PASS for `/home/yoshizawa/.codex/skills/harness`, `.claude/skills/harness`, and `.agents/skills/harness`.
- [x] Validation: `python3 -m json.tool` PASS for `.claude/settings.json`, `.claude/settings.local.json`, `.agents/settings.json`, and `.agents/settings.local.json`.
- [x] Validation: `git diff --check -- AGENTS.md CLAUDE.md .agents/AGENTS.md .claude/skills/harness/SKILL.md .agents/skills/harness/SKILL.md .claude/commands/harness.md .agents/commands/harness.md` → PASS.
- [x] Note: `.claude/commands/harness.md` exists locally but is ignored by the repository-level `.gitignore` entry `.claude/`; `.agents/commands/harness.md` is visible as an untracked counterpart.

## Completed Updates 2026-05-06 (Harness Audit Follow-up)
- [x] Ran `$harness` audit after command setup and confirmed the remaining high-impact issue: `.gitignore` still hid `.claude/commands/`, `.claude/hooks/`, and `.claude/doc/pending-tasks.md` from Git visibility.
- [x] Updated `.gitignore` to keep `.claude/commands/`, `.claude/hooks/`, and `.claude/doc/pending-tasks.md` visible while keeping session handoffs and other `.claude/doc/*` artifacts ignored.
- [x] Synced `.agents/settings.local.json` with `.claude/settings.local.json` so credit handoff, rule/skill sync reminder, Codex/rtk, gh, and Playwright permissions are aligned.
- [x] Updated `.agents/AGENTS.md` synchronization wording to explicitly include slash commands.
- [x] Validation: `python3 -m json.tool .agents/settings.local.json` and `.claude/settings.local.json` → PASS.
- [x] Validation: `git diff --check -- .gitignore .agents/settings.local.json .agents/AGENTS.md .claude/commands/harness.md .agents/commands/harness.md .claude/hooks .claude/doc/pending-tasks.md` → PASS.
- [x] Remaining note: `.agents/` counterparts are still largely untracked because the repository previously carried `.agents/` as local harness state; commit/PR scope should separate harness files from unrelated application diffs.

---

## Pending Task 3 修正 (CHECK NG → Act フェーズ)

**Check 結果: CHECK NG**

### 指摘内容
1. **[Medium]** 認証ヘッダー関数の重複（src/public/chat/main.js vs src/public/common/kyouCommon.js）
   - `buildAuthHeaders(extraHeaders)` と `getAuthHeaders()` がほぼ同一処理を重複実装
   - 修正: kyouCommon.js の `getAuthHeaders()` を export して main.js から import

2. **[Low]** localStorage アクセスの統一
   - main.js は `getAuthToken()` で取得、kyouCommon.js は直接 `localStorage.getItem()` 呼び出し
   - 修正: `getAuthToken()` を kyouCommon.js で export、そこから呼び出し

### Modified ファイル（未コミット）
```
M src/api/index.py
M src/public/chat/main.js
M src/public/common/kyouCommon.js
M run.py
?? supabase/migrations/007_conversations_user_id.sql
```

### 次フェーズ (Phase 6: Act)
- [x] `buildAuthHeaders()` 関数を main.js から削除
- [x] kyouCommon.js の `getAuthHeaders()` を export function に変更
- [x] kyouCommon.js に `getAuthToken()` export function を追加
- [x] main.js で kyouCommon から `getAuthHeaders()` を import
- [x] main.js の 3 箇所 fetch ヘッダーを修正（L427, L245, L356）
- [x] ruff check/format 通過確認
- [x] Playwright 6/6 確認
- [ ] PR作成・レビュー・マージ（既存の未コミット変更が多く、今回ターンでは Act 修正と検証まで実施）

### Act 対応結果（2026-05-06）
- [x] `src/public/chat/main.js` の認証ヘッダー生成を `getAuthHeaders()` import 利用へ統一
- [x] `src/public/common/kyouCommon.js` で `getAuthToken()` / `getAuthHeaders()` を export し、localStorage アクセスを一元化
- [x] `rg "buildAuthHeaders|getAuthHeaders|getAuthToken|kyosist_token" src/public/chat/main.js src/public/common/kyouCommon.js -n` で重複削除・参照先統一を確認
- [x] Windows Python: `python -m ruff check .` / `python -m ruff format --check .` 通過
- [x] Windows 側サーバー（`python -m uvicorn run:app --host 127.0.0.1 --port 8000`）で疎通確認（HTTP 200）
- [x] Windows Node: `cd my-playwright-project && npx playwright test` → 6/6 PASS
- [ ] PR作成・レビュー・マージは未実施。次回、作業ツリーの既存差分を確認してコミット対象を分離してから実施する

**引き継ぎドキュメント**: `.claude/doc/session-handoffs/session-handoff-2026-05-06.md` に詳細記載
