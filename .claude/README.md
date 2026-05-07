# .claude ディレクトリガイド

## 📋 概要

`.claude`ディレクトリは、MIRAIシステム開発における知識ベース、開発ルール、AI自動化アーキテクチャの中核ディレクトリです。

### MIRAIシステムの特殊性

**重要：本システムは完全独自フレームワークで構築されています。**

- **LLMが学習している一般的なコーディング方法は使用禁止**
- **Spring Boot、React、Vue.jsなどの一般的なフレームワークは使用不可**
- **Stream API、Lambda式、Boolean型の使用は禁止**
- **既存コードベースが唯一の真実**：新しいパターンを独自に考案することは禁止

### 技術スタック

- **フロントエンド**: JavaScript（独自フレームワーク：ndsUtil.js → sasCommon.js → miraiCommon.js）
- **バックエンド**: Java（独自フレームワーク：DbUtils、StringUtils、Jsml、Containerパターン）
- **データベース**: 3層構造
  - **Cassandra**（正データ）：トランザクションデータ、マスタデータ
  - **Elasticsearch**（検索）：複雑な検索、インクリメンタルサーチ
  - **MariaDB**（集計）：集計処理、レポート、CSV入出力（バッチのみ）

---

## 🏗️ ディレクトリ構造

ルート索引は [/CLAUDE.md](../CLAUDE.md) を参照。`.claude/` 配下の主要ルールファイル群:

```
.claude/
├── README.md                                   # 本ファイル
├── settings.local.json                         # ローカル環境設定
├── absolute_rules.md                           # 絶対ルール（独自FW大前提・禁止事項）
├── coding_rules.md                             # コーディング規約・参照順序
├── claude_code_behavior.md                     # Claude Code 行動ルール
├── quick_reference.md                          # 技術スタック・要点クイック参照
├── troubleshooting.md                          # FE/BE/DB トラブル対応
├── db_rules.md                                 # 3層DB使い分け
├── batch_rules.md                              # CSV取込3段階
│
├── # フロントエンド (intro 索引 + 詳細3ファイル)
├── frontend_intro_rules.md                     # FE 索引・関連ファイル一覧
├── frontend_dev_rules.md                       # FE 実装パターン
├── frontend_list_screen_rules.md               # FE 一覧画面詳細
├── frontend_detail_popup_rules.md              # FE 詳細ポップアップ
│
├── # バックエンド (intro 索引 + 詳細4ファイル)
├── backend_intro_rules.md                      # BE 索引・関連ファイル一覧
├── backend_dev_rules.md                        # BE 実装パターン
├── backend_utils_rules.md                      # BE 共通部品
├── backend_api_container_rules.md              # BE API/Container パターン
├── backend_javadoc_misc_rules.md               # BE JavaDoc・補足
│
├── # DB移行 / スキーマ (intro 索引 + 詳細3ファイル)
├── db_migration_schema_intro_rules.md          # DB移行 スキーマ 索引
├── db_migration_schema_mariadb_rules.md
├── db_migration_schema_cassandra_rules.md
├── db_migration_schema_elasticsearch_rules.md
│
├── # DB移行 / データ投入 (intro 索引 + 詳細4ファイル)
├── db_migration_dataload_intro_rules.md        # DB移行 データ投入 索引
├── db_migration_dataload_operations_rules.md
├── db_migration_dataload_csv_rules.md
├── db_migration_dataload_excel_rules.md
├── db_migration_dataload_insertgen_rules.md
│
├── # DB移行 / 単独ファイル
├── db_migration_reindex_rules.md               # リインデックス・3DB整合性・CI/CD
└── db_migration_recovery_rules.md              # リカバリ・ロールバック・トラブル対応
```

**注**: AI自動化アーキテクチャ、開発ガイド、プロジェクト管理資料は`docs/`ディレクトリに移動しました。詳細は[docs/README.md](../docs/README.md)を参照してください。

---

## 📖 ドキュメント体系

### 1. MIRAI開発ルール（必読）

プロジェクト全体のコーディング規約と実装パターン。新規参画者は最初にこれらを読むこと。

| ドキュメント | 内容 | 優先度 |
|------------|------|--------|
| **`/CLAUDE.md`** | **プロジェクト全体索引・絶対ルール** | ⭐⭐⭐ |
| `absolute_rules.md` | 独自FW大前提・禁止事項 | ⭐⭐⭐ |
| `coding_rules.md` | 独自FW遵守3項目・必須14項目・参照順序 | ⭐⭐⭐ |
| `frontend_intro_rules.md` | フロントエンド詳細実装 索引 (4分割) | ⭐⭐⭐ |
| `backend_intro_rules.md` | バックエンド詳細実装 索引 (5分割) | ⭐⭐⭐ |
| `db_rules.md` | 3層DB詳細設計・パフォーマンス最適化 | ⭐⭐⭐ |
| `batch_rules.md` | 3段階バッチ構成・CSV取込パターン | ⭐⭐ |
| `db_migration_schema_intro_rules.md` | DB移行: スキーマ変更 索引 (4分割) | ⭐⭐ |
| `db_migration_dataload_intro_rules.md` | DB移行: CSV/Excel一括投入 索引 (5分割) | ⭐⭐ |
| `db_migration_reindex_rules.md` | DB移行: リインデックス・3DB整合性・CI/CD | ⭐⭐ |
| `db_migration_recovery_rules.md` | DB移行: リカバリ・ロールバック・トラブルシューティング | ⭐⭐ |
| `troubleshooting.md` | FE/BE/DB トラブル対応 | ⭐⭐ |
| `quick_reference.md` | 技術スタック・要点クイック参照 | ⭐ |
| `claude_code_behavior.md` | Claude Code 行動ルール (承認/通知/モデル使い分け等) | ⭐ |

### 2. AI自動化アーキテクチャ（docs/architecture/）

AI駆動開発による工数削減のアーキテクチャ定義。Level 4達成で60%削減実証済み。

**注**: 以下のドキュメントは`docs/architecture/`ディレクトリに移動しました。

| ドキュメント | 対象 | 自動化タスク数 | 達成レベル | 削減率 |
|------------|------|--------------|-----------|--------|
| `docs/architecture/frontend_automation_architecture.md` | 画面FE | 3タスク（一覧系、一覧系拡張、登録系） | **Level 4達成** | **60%** |
| `docs/architecture/backend_automation_architecture.md` | 画面BE | 6タスク（search/get/update/delete/upload/download） | Level 2 | 目標60% |
| `docs/architecture/batch_automation_architecture.md` | バッチ | 6タスク（M2Net受信/UL/DL/集計/e通い箱/M2net配信） | **Level 4達成**（M2Net） | **60%** |
| `docs/architecture/db_migration_automation_architecture.md` | DB移行 | 3層DB移行自動化 | Level 3 | **50%** |

**自動化レベル定義**:
- **Level 1（完全手動）**: 0%削減
- **Level 2（スケルトン生成）**: 20%削減
- **Level 3（定型処理自動生成）**: 40%削減
- **Level 4（BL以外自動生成）**: **60%削減** ← 現在ここ
- **Level 5（完全自動生成）**: 80%+削減（将来目標）

👉 [詳細を見る](../docs/architecture/README.md)

### 3. データ移行ガイド

手動Insert vs 自動化の選択基準とベストプラクティス。

| ドキュメント | 内容 | 対象データ量 | 工数 |
|------------|------|------------|------|
| `db_migration_*_rules.md` (schema/dataload/reindex/recovery 計 11 ファイル) | DB移行自動化ルール（Cassandra/ES/MariaDB） | 大量データ | 33.5分/テーブル（50%削減） |
| `docs/data/README.md` | データ移行ディレクトリ全体ガイド | 全量 | - |
| `docs/data/migration_procedure.md` | 手動移行手順書（Excel→SQL→INSERT） | 少量データ（100件未満） | 65分/テーブル |

**選択基準**:
- **手動Insert**: 少量データ（100件未満）、緊急対応、検証環境
- **自動化**: 大量データ、本番移行、定期的な更新

### 4. 開発ガイド（docs/guides/）

AI駆動開発の実践的な手順書とプロンプト作成ガイド。

**注**: 以下のドキュメントは`docs/guides/`ディレクトリに移動しました。

| ドキュメント | 内容 | 対象読者 |
|------------|------|---------|
| `docs/guides/code_generation_guide.md` | コード生成実践ガイド | 全開発者 |
| `docs/guides/prompt_usage_guide.md` | プロンプト作成ガイド | AI利用者 |

👉 [詳細を見る](../docs/guides/README.md)

### 5. プロジェクト管理資料（docs/project-management/）

プロジェクト進捗管理、経済効果分析、自動化タスクの追跡。

**注**: 以下のドキュメントは`docs/project-management/`ディレクトリに移動しました。

| ドキュメント | 内容 | 対象読者 |
|------------|------|---------|
| `docs/project-management/ai_catchup_plan_slides.md` | AIキャッチアッププラン | 経営層・IT部門 |
| `docs/project-management/automation_task_list.md` | 自動化タスクリスト | 開発チーム |

👉 [詳細を見る](../docs/project-management/README.md)

---

## 🚀 新規参画者向けガイド

### Step 1: MIRAI固有の制約理解（最重要）

1. **`/CLAUDE.md`** を熟読（30分）
   - 独自フレームワークの絶対ルール
   - 禁止事項（Stream API、Lambda式、Boolean型）
   - 3層DB構造の理解

2. **既存コアファイルの確認**（1時間）
   - フロントエンド: `/web/common/js/{ndsUtil.js, sasCommon.js, miraiCommon.js}`
   - バックエンド: `/com.nds_rd.sas.mstl/src/main/java/com/nds_rd/lib/`

### Step 2: 詳細実装ルールの習得

3. **担当領域のルールファイルを精読**（2-3時間）
   - フロントエンド開発者: `frontend_intro_rules.md` (関連ファイル表から各詳細ファイルへ)
   - バックエンド開発者: `backend_intro_rules.md` (関連ファイル表から各詳細ファイルへ)
   - 全員: `db_rules.md`（3層DB構造の理解）

4. **サンプルコードの分析**（2時間）
   - フロントエンド: `/web/html_ssl/office/main/rcvPlan/searchRcvPlanDtlList.js`
   - バックエンド: `/com.nds_rd.sas.mstl/src/main/java/jp/co/mazdastl/api/office/rcv/SearchRcvPlanDtlList.java`

### Step 3: AI自動化の活用

5. **自動化アーキテクチャの理解**（1時間）
   - 担当領域の`docs/architecture/*_automation_architecture.md`を確認
   - プロンプトテンプレートの使い方を学習（`docs/guides/prompt_usage_guide.md`）
   - コード生成実践ガイドを確認（`docs/guides/code_generation_guide.md`）

6. **実践開発**
   - AI駆動開発で工数60%削減を実現
   - 生成コードは必ず既存パターンと比較検証

---

## 🔧 開発者向け機能

### AI自動化の活用

#### フロントエンド開発（60%削減達成）

```bash
# 一覧画面の自動生成（Level 4）
# 1. 既存の類似画面を特定
# 2. プロンプトテンプレートを適用
# 3. 生成されたコードをレビュー
# 詳細: docs/architecture/frontend_automation_architecture.md
# ガイド: docs/guides/code_generation_guide.md
```

#### バックエンド開発（目標60%削減）

```bash
# API実装の自動生成（Level 4目標）
# 1. CRUD種別を特定（search/get/update/delete）
# 2. Container パターンを適用
# 3. トランザクション処理を自動生成
# 詳細: docs/architecture/backend_automation_architecture.md
# ガイド: docs/guides/code_generation_guide.md
```

#### バッチ処理（60%削減達成 - M2Net）

```bash
# 3段階バッチの自動生成（Level 4）
# 1. Rcp[機能名]Eky（ファイル受信）
# 2. Export[機能名]ToMysqlAndCassandra（データ変換）
# 3. Export[機能名]ToElasticsearch（インデックス作成）
# 詳細: docs/architecture/batch_automation_architecture.md
# ガイド: docs/guides/code_generation_guide.md
```

#### データ移行（50%削減達成）

```bash
# 自動化移行（33.5分/テーブル）
# 1. Bean定義の自動生成
# 2. マッピングロジック生成
# 3. 3層DB同期処理生成
# 詳細: docs/architecture/db_migration_automation_architecture.md

# 手動移行（65分/テーブル）
# 1. Excelテンプレート入力
# 2. SQL生成（マクロ）
# 3. 手動実行
# 詳細: docs/data/migration_procedure.md
```

---

## 📏 運用ルール

### ファイル管理

- **追記専用**: 既存内容の削除・改変は原則禁止
- **日付記録**: 変更時は必ず日付（YYYY-MM-DD）を記録
- **サイズ制限**: 各mdファイル原則100行以内（アーキテクチャファイルは例外）
- **機密情報禁止**: APIキー、パスワード等の記載禁止

### 命名規則

- **ファイル名**: `kebab-case`（例: `frontend_intro_rules.md`）
- **拡張子**: `.md`, `.json` のみ許可
- **整理方針**: フラット構造を維持（過度な階層化を避ける）

### 品質基準

- **構文エラー**: 0件
- **リンク切れ**: 0件
- **MIRAI固有制約への準拠**: 100%

---

## 📊 AI自動化の現状と成果

### 実証済み成果（2025年10月時点）

| 領域 | タスク | 達成レベル | 工数削減率 | 実装時間 | 対象機能数 |
|------|--------|-----------|-----------|---------|-----------|
| **画面FE** | 一覧系 | **Level 4** | **60%** | 10h → 4h | 15機能 |
| **バッチ** | M2Net受信 | **Level 4** | **60%** | 8h → 3.2h | 10機能 |
| **バッチ** | 集計 | Level 2 | 20% | 8h → 6.4h | 10機能（進行中） |
| **DB移行** | 3層DB | Level 3 | **50%** | 65分 → 33.5分 | - |

### キャッチアップ効果

- **総残工数**: 133.7人月
- **AI適用後**: 94.79人月
- **キャッチアップ工数**: **38.91人月削減**
  - 開発: 30.25人月削減（50%効率化）
  - 単体テスト: 3.86人月削減（20%効率化）
  - データ移行: 4.80人月削減（50%効率化）

詳細: `docs/project-management/ai_catchup_plan_slides.md`

---

## 🔍 よくある質問（FAQ）

### Q1: 一般的なフレームワークの知識は使えますか？

**A**: 使えません。MIRAIシステムは完全独自フレームワークで構築されており、Spring Boot、React、Vue.jsなどの知識は適用できません。必ず既存コードベースを参照してください。

### Q2: Stream APIやLambda式を使ってもいいですか？

**A**: 禁止です。本システムでは通常のfor文と匿名クラスを使用します。詳細は`/CLAUDE.md`を参照。

### Q3: データベースはどれを使えばいいですか？

**A**: 用途により使い分けます。
- **Cassandra**: トランザクションデータ（画面からのCRUD）
- **Elasticsearch**: 検索（条件検索でIDリスト取得）
- **MariaDB**: 集計・レポート（バッチのみ、画面からは禁止）

### Q4: AI自動化はどのレベルまで達成していますか？

**A**: 画面FEとバッチM2Net受信でLevel 4達成（60%削減）。バックエンドはLevel 2（20%削減）です。詳細は各`*_automation_architecture.md`を参照。

### Q5: 手動データ移行と自動化、どちらを使うべきですか？

**A**:
- **100件未満の少量データ**: 手動Insert（65分/テーブル）
- **大量データ・本番移行**: 自動化（33.5分/テーブル、50%削減）

詳細: `docs/data/README.md`

---

## 📚 関連ドキュメント索引

### プロジェクト全体

- **`/CLAUDE.md`**: プロジェクト概要・絶対ルール・クイックリファレンス
- **`docs/README.md`**: ドキュメント体系全体ナビゲーション

### MIRAI開発ルール（.claude/）

- `.claude/rules/frontend/frontend_intro_rules.md`: フロントエンド詳細実装 索引 (関連ファイル表から各詳細へ)
- `.claude/rules/backend/backend_intro_rules.md`: バックエンド詳細実装 索引 (関連ファイル表から各詳細へ)
- `.claude/rules/database/db_rules.md`: データベース詳細実装
- `.claude/rules/batch/batch_rules.md`: バッチ処理詳細実装
- `.claude/rules/db_migration/schema/db_migration_schema_intro_rules.md`: DB移行: スキーマ変更 索引
- `.claude/rules/db_migration/dataload/db_migration_dataload_intro_rules.md`: DB移行: CSV/Excel一括投入 索引
- `.claude/rules/db_migration/reindex/db_migration_reindex_rules.md`: DB移行: リインデックス・3DB整合性・CI/CD
- `.claude/rules/db_migration/recovery/db_migration_recovery_rules.md`: DB移行: リカバリ・ロールバック・トラブルシューティング

### AI自動化アーキテクチャ（docs/architecture/）

- `docs/architecture/frontend_automation_architecture.md`: 画面FE自動化
- `docs/architecture/backend_automation_architecture.md`: 画面BE自動化
- `docs/architecture/batch_automation_architecture.md`: バッチ自動化
- `docs/architecture/db_migration_automation_architecture.md`: DB移行自動化
- `docs/architecture/README.md`: アーキテクチャ全体ガイド

### 開発ガイド（docs/guides/）

- `docs/guides/code_generation_guide.md`: コード生成実践ガイド
- `docs/guides/prompt_usage_guide.md`: プロンプト作成ガイド
- `docs/guides/README.md`: ガイド全体ナビゲーション

### データ移行（docs/data/）

- `.claude/rules/db_migration/schema/db_migration_schema_intro_rules.md` / `db_migration_dataload_intro_rules.md` / `db_migration_reindex_rules.md` / `db_migration_recovery_rules.md`: DB移行自動化ルール (索引から各詳細へ)
- `docs/data/README.md`: データ移行ディレクトリ全体ガイド
- `docs/data/migration_procedure.md`: 手動移行手順書

### プロジェクト管理（docs/project-management/）

- `docs/project-management/ai_catchup_plan_slides.md`: AIキャッチアッププラン
- `docs/project-management/automation_task_list.md`: 自動化タスクリスト
- `docs/project-management/README.md`: プロジェクト管理資料ガイド

---

## 📝 更新履歴

- **2026-05-01**: dangling 参照修正・README modernize (HarnessOps Step D)
  - 削除済み旧ファイル名 (`frontend_rules.md` `backend_rules.md` `db_migration_rules.md`) への参照を新分割ファイル名 (`*_intro_rules.md` 等) へ全置換
  - 行数記載を全削除 (今後の腐敗防止)
  - ツリー図・表を分割後 18 ファイル相当に更新
- **2025-10-07**: ドキュメント構造リファクタリング
  - 8ファイルを`docs/`ディレクトリに移動（architecture/guides/project-management）
  - `.claude/`は開発ルール専用ディレクトリに純化
  - 各ディレクトリにREADME.mdを追加
  - ドキュメント間の相互参照を更新
- **2025-10-07**: README.md大規模リファクタリング
  - MIRAI固有制約の明記
  - AI自動化アーキテクチャ4ファイルへの参照追加
  - データ移行ガイド追加
  - 実際のディレクトリ構造に修正（フラット構造）
  - 存在しないディレクトリ・ファイルへの参照を全削除
  - 新規参画者向けフローをMIRAI固有の学習パスに更新
  - AI自動化実績（Level 4達成、60%削減）を追加
- 2025-09-12: README.md初版作成

---

**管理者**: プロジェクトリーダー
**問い合わせ**: プロジェクトSlackチャンネル #ms-mirai-claude
