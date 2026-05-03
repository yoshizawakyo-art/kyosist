---
name: python-quality
description: Pythonバックエンドのコード品質基準とFastAPI固有のパターン
globs: ["api/**/*.py", "backend/**/*.py", "*.py"]
---

# Python 品質ルール

## 検証コマンド（Python ファイル変更後に必ず実行）
- `ruff check .` — リント（エラーがあれば修正してから完了宣言）
- `ruff format --check .` — フォーマット確認
- `ruff format .` — フォーマット自動修正

## FastAPI パターン
- レスポンスには `response_model` を指定する
- エラーは `HTTPException` で返す（辞書を直接返さない）
- 本番では `allow_origins=["*"]` を使わない（環境変数でオリジンを制御する）

## 型ヒント
- 関数引数・戻り値には型ヒントを付ける
- Pydantic モデルには全フィールドに型を付ける

## 同期ルール
- `api/index.py`（Vercel用）と `backend/main.py`（ローカル開発用）のルート定義は常に同期させる
