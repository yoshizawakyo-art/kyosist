---
name: pdca-parallel-workflow
description: Orchestrate parallel implementation of multiple issues through unified Check and integrated merge across 4 phases (Plan→Do→Check→Act). Use when running multiple features simultaneously—combines design validation to prevent contradictions and efficient Act correction while maintaining quality and boosting development velocity.
compatibility: Claude × Codex delegation, multi-issue parallel management, pdca-workflow.md compliance
---

# PDCA 並列実装ワークフロー

このスキルは、**複数 issue を効率的に並列実装・検証するための全サイクルを統括** します。

## いつ使うか（使用場面）

1. **複数機能の同時開発**（例: 認証機能 + プロフィール表示 + 通知機能を並列実装）
   - 各featureを独立issue化 → 並列Do → 統一Check（矛盾検出） → 統合Push
   
2. **緊急修正 + 既存開発の並列進行**（例: バグ修正 + 新機能開発を同時実施）
   - バグ修正 issue を優先実行 → 新機能 issue と並列化 → Check で相互影響を検証

3. **Check 指摘が多い開発サイクルの効率化**（例: 1回目Check NG → Act修正 → 再Check）
   - Act修正中に別issue の準備を並列実行 → Check再実施時に全体が完了
   - 単発issue よりも確実に開発時間を短縮

## フロー概要

```
┌─────────────────────────────────────────────────────────┐
│ P: Plan（Claude）                                      │
│   - 要件整理                                            │
│   - 実行順序・依存関係の明示                            │
│   - issue 作成                                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ D: Do（Codex 並列実行）                                │
│   - 複数issue を並列実装                               │
│   - ローカルで実装完了（git操作なし）                 │
│   - エラー時は自律的に修正（最大3回）                 │
│   - 3回失敗時は Claude に報告・停止                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ C: Check（pdca-check-reviewer）                       │
│   - 全 issue の統合レビュー                             │
│   - CHECK OK / CHECK NG を返す                        │
└─────────────────────────────────────────────────────────┘
                          ↓
             ┌───────────────────────┐
             │  CHECK OK?            │
             └───────────────────────┘
            YES ↓                ↓ NO
               │        ┌──────────────────────────┐
               │        │ A: Act（Codex）         │
               │        │ - 指摘対応               │
               │        │ - ローカル修正          │
               │        │ - 再Check（最大3回）   │
               │        └──────────────────────────┘
               │                    ↓
               │        ┌──────────────────────────┐
               │        │ C: Check再実行          │
               │        └──────────────────────────┘
               │                    ↓
               └────→ [CHECK OKまでループ]
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Codex：PR作成・マージ                                  │
│ - git add/commit/push                                  │
│ - PR作成                                               │
│ - マージ実行                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: Plan（Claude）

### 目的
複数 issue を整理し、実行順序と依存関係を明示する。

### 実施内容
1. **要件の整理**
   - 各 issue の要件を明確化
   - スコープを確定

2. **依存関係の把握**
   - issue 間に先後関係があるか確認
   - 並列実行可能か、順序必須か判定

3. **Issue 優先度の決定**
   
   以下の優先順序に基づいて、実行順序を決定する：
   
   | 優先度 | 例 | 理由 |
   |---|---|---|
   | **1. DB / スキーマ設計** | テーブル作成・マイグレーション | 後続の全 issue が依存 |
   | **2. API / バックエンド** | エンドポイント実装 | フロント・テストが依存 |
   | **3. フロント / UI** | 画面実装・イベントハンドリング | バックエンド完了後実装 |
   | **4. テスト / ドキュメント** | テスト追加・APIドキュメント | 実装完了後に追加 |
   | **5. 運用 / デプロイ** | CI/CD設定・監視設定 | 本番デプロイ前に実施 |
   
   **決定アルゴリズム**:
   ```
   1. 全 issue を優先度別に分類
   2. 同じ優先度の issue は互いに並列可能と判定
   3. 上位優先度の issue が CHECK OK になるまで、下位優先度は待機
   4. 独立した issue（他に依存しない）は、優先度に関わらず先行実行可能
   
   例:
   - issue-A（DB マイグレーション）→ 優先度 1 → 実行順序: 1番目（最初に実施）
   - issue-B（API 実装）→ 優先度 2 → 実行順序: 2番目（A完了後に実施）
   - issue-C（フロント）→ 優先度 3 → 実行順序: 2番目（B並列可、ただし A完了待ち）
   - issue-D（ドキュメント）→ 優先度 4 → 実行順序: 3番目（B/C完了後に実施）
   ```

4. **実行計画の策定**
   ```
   実行順序（優先度ベース）:
   1. issue-A（DB設計）→ 優先度: 1 → 実行順序: 1番目
   2. issue-B（API実装）→ 優先度: 2 → 実行順序: 2番目（A完了後）
   3. issue-C（フロント）→ 優先度: 3 → 実行順序: 2番目（A完了後、B並列可）
   ```

5. **Issue 作成**
   - `.claude/issue/<具体的なタスク名>/issue.md` を作成
   - 以下のテンプレートに従って記入
   - 要件・対象ファイル・優先度を明記

### Issue テンプレート（複数例）

**テンプレート基本形式**:
```markdown
# <タスク名>

## 優先度
<優先度番号: 1-5>

## 要件
- 

## 対象ファイル
- 

## レビュー結果
CHECK: false
```

**具体例 1: DB マイグレーション（優先度 1）**:
```markdown
# DB スキーマ: ユーザー認証テーブル作成

## 優先度
1

## 要件
- Supabase に `auth_users` テーブル作成
- カラム: id (PK), email (unique), password_hash, created_at
- インデックス: email に unique インデックス作成

## 対象ファイル
- supabase/migrations/001_create_auth_users.sql
- supabase/seed.sql

## レビュー結果
CHECK: false
```

**具体例 2: API 実装（優先度 2）**:
```markdown
# API: ユーザー認証エンドポイント

## 優先度
2

## 要件
- POST /api/auth/login エンドポイント実装
- email/password で Supabase 認証
- JWT トークン返却
- エラーハンドリング（401, 400）

## 対象ファイル
- src/api/index.py
- src/api/auth.py

## 依存 issue
- DB スキーマ: ユーザー認証テーブル作成（優先度 1）

## レビュー結果
CHECK: false
```

**具体例 3: フロント実装（優先度 3）**:
```markdown
# フロント: ログイン画面実装

## 優先度
3

## 要件
- ログインページ（email/password フォーム）
- API呼び出し・トークン保存
- エラーメッセージ表示
- 成功時は メインページへリダイレクト

## 対象ファイル
- src/public/login/index.html
- src/public/login/main.js

## 依存 issue
- API: ユーザー認証エンドポイント（優先度 2）

## レビュー結果
CHECK: false
```

### チェックリスト
- [ ] 全 issue の要件が明確か
- [ ] issue 間の依存関係を図示したか
- [ ] 実行順序を優先度ベースで決定したか
- [ ] 各 issue に優先度番号を明記したか
- [ ] スコープ外の内容が混ざっていないか

### 出力例
```
## Plan 結果

### Issue 一覧
1. issue-auth-migration
   - 要件: Supabase JWT認証への移行
   - 対象: src/api/index.py, src/public/common/auth.js
   - 実行順序: 1番目

2. issue-user-profile
   - 要件: ユーザープロフィール表示機能
   - 対象: src/public/profile/*, src/api/index.py
   - 実行順序: 2番目（issue-auth-migration 後）
   - 依存: issue-auth-migration

### 依存関係
issue-auth-migration → issue-user-profile

### 並列実行計画
- 実行順序 1: issue-auth-migration
- 実行順序 2: issue-user-profile
```

---

## Phase 2: Do（Codex）

### 目的
Plan で確定した複数 issue を、並列で実装する。

### 実施内容

**実行準備**
- `.claude/skills/codex-invoke/SKILL.md` の「並列issue実装」セクション参照
- issue の実行順序と依存関係を確認

**並列実装**
```bash
# Codex が以下を自動実行
1. issue-A を実装（実行順序1）
   - ローカルで実装完了
   - テスト・確認済み

2. issue-A 完了後、issue-B/C を並列実装（実行順序2）
   - issue-B と issue-C は同時進行
   - 各自でローカル実装完了
```

**複雑な依存関係がある場合の並列度調整**

実行順序が複数段階に分かれている場合、以下のルールで並列度を最適化：

```
例: issue-A → (B, C) → (D, E) → F という依存チェーン

並列度を高めるには:
- A 完了時に B/C を同時開始（待たない）
- B/C の進度によらず、両方とも進捗順に進める
- B が C より早く完了しても、D は B 完了後すぐ開始（C と並列可）
- 同じ依存レベル（D, E）は必ず並列実行

並列度を絞るには:
- API仕様の変更が多い場合は、A 完全完了 → B/C を順次実装
- DB スキーマ競合の可能性がある場合は、B/C を順次実装（並列不可）
```

**ローカル実装のみ**
- git 操作はしない（branch/push/commit 等）
- コード修正・テスト・確認のみ

**エラー時の自動対応**
- エラー発生時、Codex が自律的に修正を試みる（最大3回）
- 各試行で「何が失敗したか」を分析

**3回失敗時**
- `.claude/rules/error-recovery.md` の「3回失敗プロトコル」に従う
- 他の並列実行を停止
- Claude に報告（失敗内容・試行ログ）

### エラー発生時の詳細フロー

```
エラー発生（1回目）
  ↓
Codex が修正を試行 → テスト実行
  ├─ 成功 → Do 続行
  └─ 失敗（2回目）
       ↓
    Codex が別アプローチで修正試行
       ├─ 成功 → Do 続行
       └─ 失敗（3回目）
            ↓
         Codex が最後の試行
            ├─ 成功 → Do 続行
            └─ 失敗（3回目失敗）
                 ↓
              【3回失敗プロトコル発動】
              - 他の並列実行停止
              - Claude に報告
              - 原因分析・再プラン待機
```

### チェックリスト
- [ ] 実行順序は正しいか
- [ ] 依存関係は守られているか
- [ ] ローカルテスト・確認は完了か
- [ ] git 操作はしていないか
- [ ] 環境依存情報がハードコードされていないか
- [ ] ログ出力が適切なレベルで記述されているか
- [ ] 冪等性が確保されているか

### 出力例
```
## Do 結果

### 実装状況
✅ issue-auth-migration: 完了
   - Supabase JWT実装
   - ローカルテスト: PASS
   - ファイル: src/api/index.py, src/public/common/auth.js

✅ issue-user-profile: 完了
   - プロフィール表示機能実装
   - ローカルテスト: PASS
   - ファイル: src/public/profile/main.js, src/api/index.py

### 未解決事項
なし
```

---

## Phase 3: Check（pdca-check-reviewer）

### 目的
Do で実装された全 issue を統合レビューし、品質を厳格に検証する。

### 実施内容

**全 issue 統合レビュー**
- 複数 issue の全差分をまとめてレビュー
- 1回の `CHECK OK / CHECK NG` を返す

**審査観点**
- 要件を満たしているか
- Plan から逸脱していないか
- 設計が破綻していないか
- 依存関係は正しいか
- UI変更がある場合は画面確認済みか
- セキュリティリスクはないか
- テスト観点は不足していないか

**結果**
- `CHECK OK` → Phase 4（マージ）へ
- `CHECK NG` → Phase 4（Act）へ（指摘リスト付き）

### チェックリスト
- [ ] 全 issue の差分を確認したか
- [ ] 要件・設計との照合を完了したか
- [ ] UI変更の画面確認は済みか
- [ ] 指摘事項は優先度順にリスト化したか

### 出力例
```
## Check

### 判定
CHECK NG

### 指摘事項
1. [High] issue-auth-migration: JWTトークンの有効期限が未実装
   → 修正期待: `exp` クレーム追加、リフレッシュトークン実装
2. [Medium] issue-user-profile: エラーハンドリングが不足
   → 修正期待: ネットワークエラー・401時の画面表示
3. [Low] issue-user-profile: プロフィール画像アップロード機能が未実装
   → 要件確認: スコープ内か / スコープ外か
```

---

## Phase 4: Act（Codex）

### 目的
Check で出た指摘を修正し、Check OK を目指す。

### 実施内容

**指摘の対応**
1. Check で出た指摘をリスト化
2. 優先度順に修正を実施
3. 修正内容ごとに確認テスト実行
4. 修正完了後、再Check を実施

**ローカル修正のみ**
- git 操作なし（branch/push/commit 等）

**再Check**
- Check 完了後、指摘事項が解消されたか確認
- CHECK OK になるまで Act と Check をループ

**最大3回ループルール**
```
Check 1回目 → NG（指摘: A, B, C）
  ↓
Act 1回目（指摘対応：A, B, C 修正）
  ↓
Check 2回目 → NG（指摘: D, E）
  ↓
Act 2回目（指摘対応：D, E 修正）
  ↓
Check 3回目 → NG（指摘: F）
  ↓
Act 3回目（指摘対応：F 修正）
  ↓
Check 4回目 → OK
  ↓
【完了】
```

※ Check NG が4回目以上繰り返される場合は、要件・設計に根本的な問題がある可能性があります。
その場合は Claude に報告し、再プランを実施してください。

### チェックリスト
- [ ] Check の指摘をすべて対応したか
- [ ] 各修正をテストしたか
- [ ] 新しい問題を持ち込まなかったか
- [ ] git 操作はしていないか

### 出力例
```
## Act 1回目結果

### 対応した指摘
1. [High] JWT有効期限実装 ✅
2. [Medium] エラーハンドリング追加 ✅
3. [Low] プロフィール画像機能 → スコープ外として保留

### 修正内容
- src/api/index.py: JWTトークン生成時に `exp` 追加
- src/public/profile/main.js: ネットワークエラー・401時の alert 追加
```

---

## Phase 5: マージ（Codex）

### 目的
CHECK OK が確定したら、PR作成・push・マージを一気実行。

### 実施内容

**git 操作**
1. `git checkout -b feature/<issue-name>`
2. `git add <修正ファイル>`
3. `git commit -m "feat: <説明>"`
4. `git push -u origin feature/<issue-name>`

**PR 作成・マージ**
- PR タイトル: issue の内容が一目でわかる名前
- PR 本文:
  ```markdown
  ## 概要
  複数issue統合PR
  - issue-auth-migration
  - issue-user-profile

  ## 変更内容
  ...

  ## 確認内容
  - ローカルテスト: PASS
  - リンター: PASS
  - Check: OK
  ```

- マージ方法: `gh pr merge --merge --auto`

### 複数issue統合PR vs 個別PR の判定

実装が複数issueにまたがる場合、PR を統合するか個別にするかを決定：

**複数issue統合PR を選ぶ場合:**
- issue 間に相互依存がある（API仕様の整合性が重要）
- issue 間でコード重複を排除したい
- ほぼ同時にマージされる予定
- issue 数が 3 つ以下

**個別PR を選ぶ場合:**
- issue が独立している（依存関係なし）
- issue 間でファイル・責務が全く異なる
- マージのタイミングが異なる可能性がある
- issue 数が 4 つ以上

統合PR の例文：
```markdown
## 概要
複数issue統合PR

- issue-auth-migration: Supabase JWT認証への移行
- issue-user-profile: ユーザープロフィール表示機能
- issue-error-handling: 統一エラーハンドリング

※ これら3issueは API仕様の相互依存のため統合PR化

## 変更内容
...

## マージ方法
統合PRはすべてのissueが CHECK OK になってから一括マージ
```

### チェックリスト
- [ ] Check OK を確認したか
- [ ] コミットメッセージは明確か
- [ ] 複数issue統合 or 個別PR を判定したか
- [ ] PR本文に全issue名を記載したか（統合の場合）
- [ ] マージ完了を確認したか

---

## Issue 管理

### ディレクトリ構造
```
.claude/issue/
├── issue-auth-migration/
│   └── issue.md              ← issue定義（要件+レビュー結果）
├── issue-user-profile/
│   └── issue.md
└── closed/                   ← 完了したissueはここに移動
    ├── issue-old-feature/
    │   └── issue.md
    └── ...
```

### Issue ファイル形式

**テンプレート**:
```markdown
# <タスク名>

## 要件
- 

## 対象ファイル
- 

## レビュー結果
CHECK: false
```

**記入例**:
```markdown
# JWT認証への移行

## 要件
- Supabase JWTトークンベースの認証に移行
- 既存セッション実装を廃止
- ローカルストレージにトークン保存

## 対象ファイル
- src/api/index.py
- src/public/common/auth.js

## レビュー結果
CHECK: true
```

### Issue のライフサイクル

```
作成（Plan フェーズ）
  ↓
実装中（Do → Check → Act ループ）
  ↓
CHECK OK 確定（レビュー結果: true に更新）
  ↓
マージ判定:
  - 依存 issue があり、それが未完了 → 待機
  - 依存 issue が完了している → マージ実行
  - 他 issue と統合PR → 全 issue が CHECK OK になるまで待機
  ↓
マージ完了
  ↓
.claude/issue/closed/ に移動
```

### 部分マージのケース

複数issue並列実装で、一部issueが先に CHECK OK になる場合の対応：

**パターン1: 独立した issue は先行マージ可**
```
issue-A（認証） → CHECK OK → マージ実行 ✅
issue-B（プロフィール、Aに依存） → Check 中...
issue-C（通知、独立） → CHECK OK → マージ実行 ✅（A の完了を待たない）
```

**パターン2: 統合PR を選んだ場合は全 issue が CHECK OK まで待機**
```
issue-A/B/C が統合PR化
issue-A → CHECK OK ✅
issue-B → CHECK OK ✅
issue-C → Check NG ← 全 issue が CHECK OK になるまで待機
```

### Issue 完了時の操作
1. issue.md の `CHECK: false` を `CHECK: true` に変更
2. issue ファイルを `.claude/issue/closed/` に移動
3. `git add .claude/issue/closed/<issue>/`
4. 他の issue と合わせてコミット・マージ

---

## よくあるシナリオと対応方法

並列issue運用の実施中に遭遇しやすい状況と、その対応パターンを紹介します。

### シナリオ1: 実装中に要件が曖昧だとわかった

**状況**: Do フェーズで issue-B を実装している最中に「API 仕様が不明確」という状況が発生

**対応**:
1. Codex が issue.md に「不明点」を記録
2. Claude に報告（他の並列 issue は続行）
3. Claude が要件確認・issue.md 更新
4. issue-B を改めて Do フェーズから再スタート

### シナリオ2: 依存 issue の実装が遅れた

**状況**: issue-C（issue-A に依存）は Do の準備ができているが、issue-A がまだ Check 中

**対応**:
- issue-A を継続処理（Check → Act ループ）
- issue-C の Do を「並列待機状態」で保持
- issue-A が CHECK OK になったら、即座に issue-C の Do を開始
- issue-C と他の独立issue（issue-B）は並列実行可能

### シナリオ3: Check で想定外の指摘が多い（3つ以上）

**状況**: 全 issue 統合 Check で高い指摘密度が見つかった

**対応**:
1. 指摘を「設計ずれ」「実装不足」「新発見」に分類
2. 優先度順に Act で対応
3. Act 完了後、速やかに Check 再実施
4. Check NG が 3回以上繰り返される場合 → 要件・設計に根本問題がある可能性
   - Claude に報告・再プラン検討

### シナリオ4: 一部 issue だけが CHECK OK になった

**状況**: issue-A/B は CHECK OK だが、issue-C はまだ NG

**対応**:
- issue-C の Act は継続
- issue-A/B は「マージ待機」状態にキープ
  - **パターン① 統合PR を選んだ場合**: issue-C の CHECK OK まで全 issue を待機
  - **パターン② 個別PR を選んだ場合**: issue-A/B を先行マージ、issue-C は独立完了後マージ

### シナリオ5: Do フェーズで 3 回の修正試行に失敗した

**状況**: issue-B の実装中にエラーが 3回連続で発生し、修正が全て失敗

**詳細フロー**:
```
Do フェーズ - issue-B 実装開始
  ↓
修正試行 1 回目
  - エラー内容: [具体的エラー]
  - アプローチ: [試行1の修正方法]
  - 結果: ❌ 失敗
  ↓
修正試行 2 回目
  - エラー内容: [具体的エラー]
  - アプローチ: [試行2の修正方法]
  - 結果: ❌ 失敗
  ↓
修正試行 3 回目
  - エラー内容: [具体的エラー]
  - アプローチ: [試行3の修正方法]
  - 結果: ❌ 失敗
  ↓
【3回失敗プロトコル発動】
```

**対応ステップ（Codex 側）**:
1. ❌ 修正試行が 3回目で失敗したことを判定
2. 他の並列実行中の issue（issue-A, issue-C）の処理を即座に停止
3. 失敗詳細を以下の形式で記録・報告
   ```
   ## Do フェーズ 失敗報告

   ### 失敗した issue
   - issue-B: <タスク名>

   ### 失敗内容（3回の試行履歴）
   1. 試行 1: <修正方法> → <失敗理由>
   2. 試行 2: <別アプローチ> → <失敗理由>
   3. 試行 3: <最終試行> → <失敗理由>

   ### 現在の状態
   - ローカル修正: 未完了
   - テスト: 未実施
   - 他の並列 issue: 停止中

   ### 必要な Claude の判断
   - 要件の再確認
   - スコープの見直し
   - 実装方針の再検討
   ```

**対応ステップ（Claude 側）**:
1. Codex の報告を受け取る
2. issue-B の根本原因を分析
   - ❓ 要件が曖昧か
   - ❓ API 仕様に矛盾があるか
   - ❓ 環境セットアップが不足しているか
   - ❓ 技術的に実装困難か
3. issue.md を修正 / 要件を明確化
4. 以下のいずれかを判定
   - 🔄 **再度 Plan から開始**: 要件見直し後、issue-B を改めて Do フェーズから再スタート
   - 🚫 **issue-B をスコープ外とする**: 本当に必要か、別タスクとするか判定
   - ✏️ **部分スコープに変更**: 実装可能な範囲に削減して再実行
5. 判定内容を Codex に報告
6. 他の並列実行再開（issue-A/C の処理を再開）

**避けるべき対応**:
- ❌ エラーログを見ずに「もう一度やってみてください」と指示
- ❌ 要件を確認しないまま「別アプローチで試してください」と指示
- ❌ issue-B の失敗をそのままにして他の issue を先進める

---

## エラーハンドリング

詳細は `.claude/rules/error-recovery.md` を参照してください。

このセクションでは、error-recovery.md で定義されたプロトコルの pdca スキル内での適用例を示します。

---

## 運用・品質ガイドライン

すべての実装フェーズで以下の運用規約を遵守する必要があります。詳細は `.claude/rules/operations.md` / `.agents/rules/operations.md` を参照。

### 環境依存情報のハードコード禁止

DB接続情報・APIキー・シークレット等はコードに直書きしない。必ず環境変数経由で読み込む。

```python
# NG
API_KEY = "sk-abc123"

# OK
import os
API_KEY = os.environ["API_KEY"]
```

**チェック方法**: コード中に API キーやシークレットが直書きされていないか確認

### ログ出力の規律

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

**チェック方法**: `print()` がデバッグ目的で残されていないか、ログレベルが適切か確認

### 冪等性（べきとうせい）の確保

ネットワークエラー等で処理がリトライされた場合でも、データの二重登録やシステム不整合が起きない設計にする:
- INSERT前にDUPLICATE CHECK（または `ON CONFLICT` / `upsert`）
- 外部API呼び出しには冪等キーを使用

**チェック方法**: DB INSERT / 外部API呼び出しでリトライ時の重複排除機構があるか確認

### 複雑なロジックへの ADR・コメント

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

**チェック方法**: 複雑なロジック・非自明な設計判断に背景コメントがあるか確認

### Check フェーズでの確認項目

Check 実施時に以下も確認する:
- 環境依存情報がコードに混入していないか
- ログ出力が適切か
- 冪等性が確保されているか
- 設計背景の記述が不足していないか

---

## 完了条件

以下をすべて満たした場合のみ完了：

- [ ] Plan を実施（全 issue 作成、依存関係明示）
- [ ] Do で全 issue 実装完了（ローカルテスト PASS）
- [ ] 運用規約を遵守（環境変数・ログ・冪等性・設計記述）
- [ ] Check で全 issue 統合レビュー完了（CHECK OK）
- [ ] Act で指摘対応完了（最大 Check 3回）
- [ ] マージ実行完了
- [ ] issue ファイルを closed/ に移動
- [ ] PR作成・マージが完了

---

## リファレンス

- Issue テンプレート: `.claude/issue/template.md`
- エラー対応: `.claude/rules/error-recovery.md`
- Codex 並列実装: `.claude/skills/codex-invoke/SKILL.md`（並列issue実装セクション）
- PDCAワークフロー詳細: `.claude/rules/pdca-workflow.md`（旧版参考）
