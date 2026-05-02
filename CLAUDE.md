# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Frontend**: HTML, CSS, Vanilla JavaScript (no framework)
- **Backend**: Python + FastAPI
- **Communication**: REST API via `fetch()`

## Commands

### Backend (local dev)

```bash
# Start dev server (from backend/ directory) — also serves public/ as static files
uvicorn main:app --reload

# Or double-click start.bat from the project root
```

### Frontend

Static files live in `public/`. In production they are served by Vercel's CDN automatically.

## Architecture

```
kyosist/
├── api/            # Vercel serverless function
│   └── index.py   # FastAPI app (API routes only)
├── backend/        # Local dev server
│   ├── main.py    # FastAPI app + StaticFiles mount for public/
│   └── requirements.txt
├── public/         # Static HTML/CSS/JS (served by Vercel CDN or local uvicorn)
│   ├── index.html
│   └── main.js
├── requirements.txt  # For Vercel Python runtime
├── vercel.json       # Vercel routing config
└── start.bat         # One-click local launcher (Windows)
```

- REST endpoints are under `/api/`.
- The frontend calls them via relative URL `/api/chat` (works on both localhost and Vercel).
- Local dev: `start.bat` → uvicorn on `http://localhost:8000` (serves `public/` + API).
- Production: Vercel CDN serves `public/`, `api/index.py` handles `/api/*` as serverless function.

## Things to Avoid
- `allow_origins=["*"]` を本番コードに残す（開発中は許容）
- `api/index.py` と `backend/main.py` を非同期に編集する（両ファイルのルートは常に同期させる）
- 環境固有の値をハードコードする（env var を使う）
- ローカル/Vercel の二重デプロイ構造を壊す変更をする

## Verification
完了宣言の前に必ず実行:
```bash
ruff check .
ruff format --check .
```

## Action Scope
自律的に進めてよい操作: `public/`, `api/`, `backend/` 内のファイル編集

必ず確認してから行う操作: git push・デプロイ実行、ファイル削除、依存パッケージの追加・変更

## Behavioral Rules
- **サブエージェント移譲・最適選択必須**: 委譲できる作業は必ずサブエージェントに移譲し、タスクの性質に応じて最適なサブエージェントタイプを選択する（詳細: `.claude/rules/subagent-selection.md`）
- **コマンド解説**: コマンド実行許可を求める際は、そのコマンドの目的を必ず日本語で説明する
- **ラムダ式禁止**: すべての言語でラムダ式・無名関数を使わない（詳細: `.claude/rules/coding-standards.md`）
- **危険コマンド警告必須**: いかなるモードでも危険なコマンドはユーザへの警告と明示的承認が必須（詳細: `.claude/rules/safety.md`）
- **完了通知**: タスク完了・承認要求時は音で通知する（Stop hookで自動実行）
- **TODO化と逐次消化**: 作業着手前に必ず TaskCreate でタスクを細分化し、1つ完了したら TaskUpdate で完了マークしてから次へ進む

詳細ルール: `.claude/rules/` 配下を参照
