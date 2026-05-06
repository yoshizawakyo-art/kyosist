# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Frontend**: HTML, CSS, Vanilla JavaScript (no framework)
- **Backend**: Python + FastAPI
- **Communication**: REST API via `fetch()`

## Commands

### Backend (local dev)

```bash
# Start dev server — serves src/public/ as static files + API
python run.py

# Or double-click start.bat from the project root
```

### Lint / Format

```bash
ruff check .
ruff format --check .
ruff format .   # auto-fix
```

## Architecture

```
kyosist/
├── api/
│   └── index.py          # Vercel エントリ（src/api/index.py を import するだけ）
├── src/
│   ├── api/
│   │   ├── index.py      # FastAPI アプリ本体（全ルート定義）
│   │   └── agent_service.py  # AIエージェントサービス層
│   └── public/           # 静的ファイル（Vercel CDN / ローカル uvicorn）
│       ├── index.html
│       ├── favicon.png
│       ├── common/       # 複数機能で共有するユーティリティ
│       │   ├── base.css
│       │   ├── kyouCommon.js
│       │   └── kyouUtils.js
│       └── chat/         # チャット機能
│           ├── index.html
│           ├── main.js
│           └── style.css
├── supabase/             # DB マイグレーション
├── run.py                # ローカル開発サーバー起動スクリプト
├── vercel.json           # Vercel ルーティング設定
└── start.bat             # ワンクリック起動（Windows）
```

- REST エンドポイントは `/api/` 配下。
- フロントエンドは相対 URL `/api/...` で呼び出す（ローカル・Vercel 共通）。
- ローカル: `run.py` → uvicorn（`src/public/` 静的配信 + API）。
- 本番: Vercel CDN が `src/public/` を配信、`api/index.py`（プロキシ）→ `src/api/index.py` が `/api/*` を処理。
- 機能固有コードは `src/public/<feature>/`、共有コードは `src/public/common/` に配置。

## Things to Avoid
- `allow_origins=["*"]` を本番コードに残す（開発中は許容）
- `api/index.py`（Vercelプロキシ）を直接編集する（実装は `src/api/index.py` に書く）
- 環境固有の値をハードコードする（env var を使う）
- ローカル/Vercel の二重デプロイ構造を壊す変更をする
- `src/public/common/` に Kyosist 固有ロジックを混入する（フレームワーク層として保つ）

## Verification
完了宣言の前に必ず実行:
```bash
ruff check .
ruff format --check .
```

## Action Scope
自律的に進めてよい操作: `src/public/`, `src/api/` 内のファイル編集

必ず確認してから行う操作: デプロイ実行、ファイル削除、依存パッケージの追加・変更

git 操作（コミット・プッシュ・PR作成）は `.claude/skills/git-push/SKILL.md` のワークフローに従う

## Behavioral Rules
- **日本語対応必須**: いかなる状況でも日本語で対応する。メッセージ、説明、エラー、質問、すべて日本語。例外なし。
- **サブエージェント移譲・最適選択必須**: 委譲できる作業は必ずサブエージェントに移譲し、タスクの性質に応じて最適なサブエージェントタイプを選択する（詳細: `.claude/rules/subagent-selection.md`）
- **コマンド解説**: コマンド実行許可を求める際は、そのコマンドの目的を必ず日本語で説明する
- **ラムダ式禁止**: すべての言語でラムダ式・無名関数を使わない（詳細: `.claude/rules/coding-standards.md`）
- **危険コマンド警告必須**: いかなるモードでも危険なコマンドはユーザへの警告と明示的承認が必須（詳細: `.claude/rules/safety.md`）
- **完了通知**: タスク完了・承認要求時は音で通知する（Stop hookで自動実行）
- **タスク管理の厳格化**: 
  - 作業着手前に必ず TaskCreate でタスクを細分化する
  - 作業開始時に TaskUpdate で `status: "in_progress"` に設定する
  - **タスク完了時に必ず TaskUpdate で `status: "completed"` に設定する**（例外なし）
  - 1つのタスクが完了したら、その都度 TaskUpdate でマークしてから次のタスクに進む
  - ユーザーへの報告では、完了したタスクを明記する
- **Task Ledger更新必須**:
  - 継続作業の開始時は `.claude/doc/pending-tasks.md` を読む
  - 実装・PR更新・マージ・ブランチ削除・検証結果など、タスク状態が変わったら同じターンで `.claude/doc/pending-tasks.md` を更新する
  - ファイル変更・検証結果・タスク状態・ブロッカー・次ステップが変わる作業後は、ルール/ドキュメントのみの小変更でも、最終応答前に必ず `.claude/doc/pending-tasks.md` を更新する
  - 完了作業は `[x]`、未実行・環境制約・保留事項は `[ ]` と理由つきで記入する
  - `.claude/doc/pending-tasks.md` 更新前に完了宣言しない
- **ルール / Skill 整合性必須** (Codex ↔ Claude 双方向同期):
  - Claude 側でルール・スキル・フックを追加・更新した場合：
    - `.claude/` 配下のファイル更新
    - **必ず** `.agents/` 配下の対応ファイルも同じターンで更新
    - `.agents/AGENTS.md` にも変更を反映（ルール一覧・実行フロー）
  - Codex 側の skill やルールを追加・更新した場合：
    - `.agents/` 配下の対応ファイル更新
    - **必ず** `.claude/` 配下の対応ファイルも同じターンで確認・更新
    - `CLAUDE.md` のルール記載を同期
  - 同期対象なしまたは意図的に非同期にする場合：
    - 理由を `.claude/doc/pending-tasks.md` または最終報告に明記
  - **同期チェックリスト**（新規追加時）:
    - ファイル作成: `.claude/` と `.agents/` 両方に
    - Skill 作成: `.claude/skills/` と `.agents/skills/` 両方に
    - Slash command 作成: `.claude/commands/` と `.agents/commands/` 両方に
    - フック登録: `.claude/settings.local.json` と `.agents/settings.local.json` 両方に
    - ドキュメント：`CLAUDE.md` と `.agents/AGENTS.md` 両方に記載
- **Check必須**: `.py` `.js` `.html` `.css` `.json` 等のコードファイルを変更したら、完了宣言の前に必ず `.claude/agents/pdca-check-reviewer.md` ガイドラインに従って超厳格にCheckを実施する。1行の修正・設定ファイルのみの変更でも例外なし（詳細: `.claude/rules/pdca-workflow.md`）

詳細ルール: `.claude/rules/` 配下を参照

## Development Workflow
すべての実装・修正タスクは以下の順で自律実行する（指示なしで完遂すること）:
```
Do → Check（.claude/agents/pdca-check-reviewer.md ガイド準拠）→ PR作成（git-push skill）
  → PR最終レビュー（.claude/agents/pdca-check-reviewer.md ガイド準拠）
  → 指摘あり: 修正 → 直接push（新規PR不要）→ PR最終レビューに戻る
  → 指摘なし: マージ（gh pr merge --merge --auto）
```
詳細: `.claude/rules/pdca-workflow.md`

## クレジット残量 5% 未満時の引き継ぎ対応

**自動実行ルール**: クレジット残量が 5% 未満に低下した時点で、以下を自律実行する：

1. **引き継ぎドキュメント作成**
   - ファイル名: `.claude/doc/session-handoffs/session-handoff-<YYYY-MM-DD>.md`
   - 内容: 現在の実装状況・CHECK フェーズ結果・修正が必要な指摘・次のセッションでの作業フロー・参考コマンド
   - タイミング: クレジット 5% 未満を検知した直後

2. **記載すべき内容**
   - セッション終了日時
   - 完了フェーズ（Task 1/2/3 の進捗）
   - Modified ファイル一覧
   - テスト結果（Playwright / ruff）
   - CHECK / CHECK NG の指摘内容と修正手順
   - 次のセッションでの作業コマンド
   - 完了条件（Definition of Done）
   - 参考情報（前セッション完了事項・注意点）

3. **ユーザーへの報告**
   - 引き継ぎドキュメント作成完了を通知
   - 修正内容と修正コマンドを簡潔に要約
   - 新しいセッションでの開始指針を提示

4. **禁止事項**
   - クレジット 5% で修正を途中まま進めない
   - 修正コマンドを実行して不完全に終わらない
   - CHECK フェーズの指摘を放置したままセッションを終了しない
