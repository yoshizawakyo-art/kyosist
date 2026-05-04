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
- **Check必須**: `.py` `.js` `.html` `.css` `.json` 等のコードファイルを変更したら、完了宣言の前に必ず `pdca-check-reviewer` を起動してCheckを実施する。1行の修正・設定ファイルのみの変更でも例外なし（詳細: `.claude/rules/pdca-workflow.md`）

詳細ルール: `.claude/rules/` 配下を参照

## Development Workflow
すべての実装・修正タスクは以下の順で自律実行する（指示なしで完遂すること）:
```
Do → Check（pdca-check-reviewer）→ PR作成（git-push skill）→ PR最終レビュー（/review skill）
  → 指摘あり: 修正 → 直接push（新規PR不要）→ PR最終レビューに戻る
  → 指摘なし: マージ（gh pr merge --merge --auto）
```
詳細: `.claude/rules/pdca-workflow.md`
