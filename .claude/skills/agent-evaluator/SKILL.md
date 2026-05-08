---
name: agent-evaluator
description: Automatically evaluate and improve skills iteratively until 95+ points. Use when a skill's SKILL.md needs enhancement for clarity, trigger conditions, or implementation feasibility. Runs max 10 improvement cycles with automated proposal generation, convergence detection, and final quality validation.
compatibility: |
  - skill-evaluator (scoring engine)
  - Codex for SKILL.md edits
  - project rules integration
---

# Agent Evaluator: スキル自動改善スキル

## 目的

サブエージェント型スキル（SKILL.md を持つスキル）を自動採点し、**スコアが95点以上になるまで反復改善し続ける**スキルです。

1回の呼び出しで、複数の改善サイクルを自動的に実行します。ユーザーの手作業を最小化しながら、スキルの品質を確実に向上させます。

## 使い方

### 基本形式

```
/skill-optimizer <path-to-skill>
```

**例:**
```
/skill-optimizer C:\Develop\Projects\Kyosist\.claude\skills\my-skill
```

### 入力（必須）

- **path-to-skill**: スキルディレクトリへの絶対パス
  - SKILL.md、およびスキルファイル（scripts/, references/ など）を含むディレクトリ

### 出力

- **改善済みスキル**: SKILL.md とスキル構造が 95点以上に最適化された形
- **改善ログ**: 各イテレーションの採点結果と改善内容
- **最終スコア**: 95点以上が達成された場合の最終スコア

## ワークフロー

### Phase 1: 初期評価

```
1. skill-evaluator を使用してスキルを採点（0-100点）
2. スコアと詳細フィードバックを取得
3. スコア ≥ 95 の場合 → 完了
   スコア < 95 の場合 → Phase 2 に進む
```

### Phase 2: 改善提案の生成

スコア < 95 の場合、skill-evaluator の採点結果から以下を自動生成：

**入力**: skill-evaluator の詳細フィードバック（失点箇所・失点理由・改善案）

**出力（改善提案）**:
1. **Critical 優先度**: トリガー説明・手順の実行可能性の欠陥
2. **High 優先度**: セクション構造の改善・例の追加
3. **Medium 優先度**: 文言の明確化・冗長性削除
4. **Low 優先度**: フォーマット・表記の統一

**生成例**:
```
Score: 68/100

Critical Issues:
- トリガー条件が曖昧 → 「いつ使うか」を3つ以上の具体例で明示化
- 手順が「改善する」だけ → ステップ 1-5 を順番付きで具体化

High Issues:
- スキル構造が冗長 → セクション統合提案 (A+B → AB)
- 例が抽象的 → 実例ベースの例に置き換え

Medium Issues:
- 説明文が長い → 簡潔化（現行 X 行 → 目標 Y 行）
```

### Phase 3: SKILL.md 更新と反復（最大 10 回）

```
Iteration 1-10:
  1. 改善提案（Critical → High → Medium → Low 優先度）を実装
  2. SKILL.md 更新 + scripts/ / references/ も調整
  3. skill-evaluator で再採点
  4. スコア確認
  
  IF スコア ≥ 95:
    → Phase 4（完了）へ
  ELIF スコア > 前回スコア:
    → Iteration N+1 へ続行
  ELIF スコア = 前回スコア × 2 回連続:
    → **停滞判定** → Phase 4b（ユーザー報告）
  ELIF Iteration = 10:
    → **上限到達** → Phase 4b（ユーザー報告）
  ELSE:
    → 次のイテレーション
```

**停滞判定の詳細**:
- スコアが 2 イテレーション連続で変わらない
- または 1 ポイント未満の改善しか見込めない
- ⇒ スキルの根本的な役割不明確の可能性

### Phase 4a: 完了（スコア ≥ 95）

```
- 改善済み SKILL.md を出力
- イテレーション履歴を記録
- improvement_log.md に成功報告を記載
- タスク完了
```

### Phase 4b: ユーザーへの報告（停滞 or 上限到達）

```
停滞判定・上限到達時：
1. 現在のスコア・イテレーション数を報告
2. 改善の課題（例: トリガー条件の役割不明確）を分析
3. ユーザーへの確認項目を提示
  - スキルの本来の役割は何か？
  - トリガー条件をどう定義すべきか？
  - 除外すべきセクションは？
4. 手動修正後の再実行を提案
```

## イテレーション戦略

### 改善対象（優先順）

1. **SKILL.md の指示文（Wording）**
   - 曖昧な表現を具体化
   - トリガー条件を明確化
   - 例やアンチパターンを追加

2. **スキルの構造・セクション**
   - 重要な説明が足りないセクションを追加
   - 無駄なセクションを削除
   - 流れを改善

3. **テストケース（evals.json）**
   - エッジケースを追加
   - 現在のテストが本当に意図通りか確認
   - 不足している観点を追加

4. **引き込み機能（Description 最適化）**
   - スキルが正しいタイミングで呼ばれるよう調整
   - キーワード・フレーズの最適化

### 各イテレーションの出力

各改善サイクルの終了時に以下を記録：

```markdown
## Iteration N

### 評価スコア
- **前回**: XX点
- **今回**: YY点
- **改善幅**: +Z点

### 実施した改善
1. [改善内容1]
2. [改善内容2]
...

### 次のステップ
- [次に改善すべき項目]

---
```

## 制限事項・前提

- **スキル形式の要件**: SKILL.md が必須（ないスキルは処理不可）
- **ループ制限**: 最大 10 回（スコア ≥ 95 または停滞判定で終了）
- **停滞判定**: スコア 2 回連続横這い → ユーザー報告・停止
- **上限判定**: Iteration 10 に到達 → ユーザー報告・停止
- **更新対象**: SKILL.md、evals.json、scripts/、references/ など
- **保護項目**: スキルの本質的な役割は変えない（採点基準で判定）
- **パフォーマンス**: 1 イテレーション = 約 1〜3 分（スキルの規模による）

## 成功例

### 例1: 新規スキルの自動最適化

```bash
/skill-optimizer /path/to/new-skill
```

→ 初期スコア: 68点
→ Iteration 1: 説明文を具体化 → 76点
→ Iteration 2: テストケース追加 → 82点
→ Iteration 3: セクション整理 → 91点
→ Iteration 4: キーワード最適化 → 96点 ✓完了

### 例2: 既存スキルの改善

```bash
/skill-optimizer /path/to/existing-skill
```

→ 初期スコア: 73点
→ [3イテレーション後]
→ 最終スコア: 95点 ✓完了

## トラブルシューティング

### スコアが改善しない場合

- **原因**: 改善提案が本質的な問題を見落としている可能性
- **対処**: 手動で SKILL.md を見直し、ユーザーが修正してから再実行

### スキルが壊れた場合

- **原因**: 極端な改善提案が実装された
- **対処**: git で前のバージョンに戻すか、手動で修正

### ループが無限に続く場合

- **原因**: スキル自体の役割が曖昧すぎる
- **対処**: skill-evaluator の採点基準を確認し、スキルの役割を明確化してから再実行

## 内部仕様

### 採点基準（skill-evaluator に準じる）

- **SKILL.md の構造・明確性**: 30点
- **指示の実用性・実装可能性**: 30点
- **トリガー条件・説明の適切性**: 20点
- **テストケース・評価方法**: 10点
- **全体的な完成度**: 10点

### イテレーション時の判定

```
IF スコア ≥ 95:
  → Phase 4a（完了）
ELIF Iteration ≥ 10:
  → Phase 4b（ユーザー報告・停止）
ELIF スコア = 前々回スコア かつ スコア = 前回スコア:
  → 停滞判定（2 回連続横這い）→ Phase 4b
ELIF スコア > 前回スコア:
  → 改善継続 → Iteration N+1
ELSE（スコア < 前回スコア）:
  → 改善案の見直し必要 → Claude に報告
```

