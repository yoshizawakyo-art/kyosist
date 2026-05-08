# ペンディングタスク一覧

最終更新: 2026-05-06

---

## ✅ 完了済み

### チャット型自動実行スキル化
- [x] `.codex/skills/automation-task-skillizer/SKILL.md` を追加し、チャット形式の作業説明からブラウザ操作・ローカルファイル操作を含む自律実行ワークフローと再利用可能 Skill を作れるようにした
- [x] `.codex/skills/automation-task-skillizer/evals/evals.json` に browser+local、local-only、危険操作確認の 3 ケースを追加
- [x] `.claude/skills/automation-task-skillizer/` に同等 Skill/evals を同期
- [x] 欠落していた `.claude/doc/pending-tasks.md` を `.codex/doc/pending-tasks.md` と同期して復旧

### codex-invoke スキル最適化（iteration-2）
- [x] 段階的タスク分割戦略を SKILL.md に追記
- [x] evals.json に staged テストケース（id=4,5,6）追加
- [x] iteration-2 ベンチマーク実行 → 100% pass rate 達成（iteration-1 は 60%）
- [x] Path A（iteration-2 で最適化して本番投入）を採用・完了

### 認証基盤ファイル実装（マージ済み）
- [x] `src/api/schemas/auth.py` — LoginRequest（EmailStr + min_length=8）/ TokenResponse
- [x] `src/api/schemas/__init__.py`
- [x] `src/api/auth_service.py` — verify_password (bcrypt) / create_access_token (JWT) / authenticate_user

### PDCAワークフロー整備
- [x] `pdca-check-reviewer` エージェント作成（model: opus, color: red, CHECK OK/NG 専用）
- [x] `.claude/rules/pdca-workflow.md` — Phase 3 Check に pdca-check-reviewer 必須使用を明記
- [x] `.claude/rules/subagent-selection.md` — pdca-check-reviewer 追加
- [x] `CLAUDE.md` — Check 担当を pdca-check-reviewer に変更
- [x] `.claude/rules/error-recovery.md` — 新規作成（エラー発生時のルール更新プロトコル）

---

## 🔲 未完了・引き継ぎ事項

### ブランチ上の未処理（fix/main-js-import-not-loaded）

PR が未作成。以下の変更がコミット済み・未PR:
- `pdca-check-reviewer.md` / `error-recovery.md` / `pdca-workflow.md` / `subagent-selection.md` / `CLAUDE.md`

未コミット変更あり:
- `run.py` — `from api.index import app` の行が削除された状態（本来のブランチ目的であるインポート修正に関連）
- `.agents/`, `.codex/`, `skills/` 配下の codex-skill-creator スクリプト群（lint 自動修正）
- `package.json` / `package-lock.json`（未追跡・要確認）

### 認証機能実装（メイン実装フェーズ）

#### フェーズ 1: バックエンド認証基盤

**Task 1-1: DB マイグレーション**
- [ ] 005_authentication.sql を確認して `supabase db push` 実行
- 参照: `supabase/migrations/`

**Task 1-2: 認証エンドポイント**
- [ ] FastAPI エンドポイント: `POST /api/auth/login` を `src/api/index.py` に追加
  - auth_service.py / schemas/auth.py はすでに実装済み → 統合するだけ
  - HTTPException 401 on failure / response_model=TokenResponse
- [ ] エラーハンドリング（401/500）

**Task 1-3 〜 1-6**
- [ ] JWT ミドルウェア実装
- [ ] ユーザーセッション管理
- [ ] トークンリフレッシュ
- [ ] ログアウト処理

#### フェーズ 2: フロントエンド認証 UI

- [ ] ログインフォーム（`src/public/auth/login.html`）
- [ ] フォームバリデーション
- [ ] `/api/auth/login` との API 統合
- [ ] JWT トークン localStorage 管理
- [ ] エラー表示

---

## 実装方針（確定）

- 実装は `codex exec --dangerously-bypass-approvals-and-sandbox` 経由で Codex に移譲
  - `mcp__codex-cli__ask-codex` は `--full-auto` エラーが出るため Bash 直接実行
- Do → Check（`pdca-check-reviewer`）→ PR作成 → PR最終レビュー → マージ のワークフロー
- 複雑な実装（複数ファイル・多依存）は Stage 分割で token limit を回避
- Task 1-2 は schemas/auth_service が完成済みなので Stage 1個（endpoint のみ）で完結する見込み
