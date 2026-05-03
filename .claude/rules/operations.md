---
name: operations
description: 運用規約（環境変数管理、ログレベル、冪等性、ADR、トークン最適化）
---

# 運用規約

## 環境依存情報のハードコード禁止

DB接続情報・APIキー・シークレット等はコードに直書きしない。
必ず環境変数（`.env` + `python-dotenv`、または Vercel 環境変数）経由で読み込む。

```python
# NG
API_KEY = "sk-abc123"

# OK
import os
API_KEY = os.environ["API_KEY"]
```

## ログ出力の規律

標準出力（`print`）をデバッグ用に残さない。適切なログレベルを使い分ける:
- `INFO`: 正常な処理フロー
- `WARN`: 想定外だが継続可能な状態
- `ERROR`: 処理失敗、要調査

```python
import logging
logger = logging.getLogger(__name__)
logger.info("処理開始: user_id=%s", user_id)
logger.error("DB接続失敗: %s", exc, exc_info=True)
```

## 冪等性（べきとうせい）の確保

ネットワークエラー等で処理がリトライされた場合でも、データの二重登録やシステム不整合が起きない設計にする:
- INSERT前にDUPLICATE CHECK（または `ON CONFLICT` / `upsert`）
- 外部API呼び出しには冪等キーを使用

## 複雑なロジックへの ADR・コメント

「なぜその設計にしたのか」という背景を残す:
- 複雑なロジックには JSDoc/docstring で設計背景を記述
- アーキテクチャ上の重要な決定は `.claude/doc/adr/` 配下に ADR として記録

```python
def calculate_fee(amount: int) -> int:
    """手数料を計算する。
    
    Note: 手数料率は2024年4月改定の料金テーブルに基づく。
    変更時は billing_config.py も合わせて更新すること。
    """
```

## AIトークン消費の最適化

- 不要なファイルをコンテキストに読み込まない
- 回答は修正したコードブロックのみを出力する（変更のない部分を再掲しない）
- 大量ファイル読み込みが発生する調査はサブエージェント（Exploreタイプ）に委任する
