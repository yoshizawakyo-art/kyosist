---
name: already-good-skill
description: |
  テストファイル群からバグを検出し、自動生成レポートを作成するスキル。
  
  適用場面：
  - ユーザーが「このテストスイートから潜在バグを検出して」と言ったとき
  - 複数テストが失敗していて、根本原因を調べたいとき
  - テスト駆動開発（TDD）で失敗パターンを分析したいとき
  
  このスキルは実装・テスト・レポート生成の 3 ステップで完全な分析を提供します。
---

# Test Bug Detection & Report Generation Skill

## 目的

テストファイル群から潜在的なバグパターンを検出し、構造化レポートを自動生成するスキル。
開発者が手作業で分析する時間を削減し、バグの根本原因を素早く特定できます。

## 使い方

### 基本形式

```
/detect-test-bugs <path-to-test-files>
```

**例:**
```
/detect-test-bugs ./tests/unit/
/detect-test-bugs ./spec/integration/auth.test.ts
```

### 入力

- **path-to-test-files**: テストファイルまたはテストディレクトリへのパス
  - 対応形式: `.test.js`, `.test.ts`, `.spec.py`, `.test.go` など

### 出力

- **Bug Detection Report** (JSON / Markdown)
  - 検出されたバグパターン（優先度順）
  - 各バグの深刻度（Critical / High / Medium / Low）
  - 修正提案コード
  - テストカバレッジギャップ分析

## ワークフロー

### Phase 1: テストファイル解析

```
1. テストファイル群を読み込む
2. テストの失敗パターンを分類
   - アサーション失敗
   - タイムアウト
   - セットアップエラー
   - リソースリーク
3. 共通パターンを検出
```

### Phase 2: バグパターン特定

```
1. エッジケースの未処理を検出
2. 非決定的（flaky）テストを識別
3. 依存関係の不足を分析
4. モック誤用パターンを検出
```

### Phase 3: レポート生成

```
1. 検出されたバグを優先度順にソート
2. 修正提案コードを含めたレポート作成
3. テストカバレッジギャップを可視化
4. JSON / Markdown の 2 形式で出力
```

## トラブルシューティング

### テストファイルが見つからない場合

```
Error: No test files found in the specified directory.
Supported patterns: *.test.js, *.test.ts, *.spec.py, *.test.go
```

確認事項：
- パスが正しいか確認
- テストファイルが標準的な命名規則に従っているか

### バグが検出されない場合

- テストカバレッジが十分に高い（すべてのエッジケースがテストされている）
- または、既知パターンのバグ実装がない

## 制限事項

- 実行されたテスト出力の分析に依存（静的解析ではない）
- ランタイムエラーのみを検出（論理バグは部分的）
- テストが実行可能な状態である必要がある

## 成功例

### 例1: 非決定的テスト検出

```
Input: ./tests/async/
Output:
- 🔴 Critical: Race condition in timeout handler
  Suggestion: Add proper await/barrier
- 🟡 High: Flaky date-based test
  Suggestion: Use frozen time (e.g., jest.useFakeTimers)
```

### 例2: エッジケース検出

```
Input: ./spec/auth.test.ts
Output:
- Coverage gap: null/undefined inputs not tested
- Coverage gap: UTF-8 special characters in email validation
- Suggestion: Add test cases for these scenarios
```

