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

## クレジット残量 5% 未満時の引き継ぎ対応（Critical Rule）

Claude のクレジット残量が 5% 未満に低下した場合、以下を**自動実行**する:

### 1. 引き継ぎドキュメント作成（最優先）

ファイル名: `.claude/doc/session-handoffs/session-handoff-<YYYY-MM-DD>.md`

必須内容:
- セッション終了日時
- 完了フェーズ（現在の Task / Phase 進捗状況）
- Modified ファイル一覧・git status
- テスト結果（Playwright / ruff check/format）
- CHECK OK / CHECK NG の判定と指摘内容（ある場合）
- 修正が必要な指摘の詳細（重要度・修正箇所・期待される修正内容）
- 次のセッションでの実行コマンド（Codex exec コマンド全文）
- 完了条件（Definition of Done）
- 参考情報（前セッション完了事項・注意点・既知制約）

### 2. User への報告

- 引き継ぎドキュメント作成完了を明記
- 修正内容・修正コマンドを簡潔に要約
- 次セッション開始の指針を提示

### 3. 禁止事項（Absolute）

- ❌ クレジット 5% で実装を途中のまま進める
- ❌ 不完全な修正コマンドを実行して終わる
- ❌ CHECK NG 指摘を放置したままセッションを終了
- ❌ 本来 Codex で実行すべき修正を Claude が直接実装する
- ❌ 引き継ぎドキュメントなしで終了する

### 4. 詳細ガイド

詳細ルール: See `CLAUDE.md` → "クレジット残量 5% 未満時の引き継ぎ対応"
