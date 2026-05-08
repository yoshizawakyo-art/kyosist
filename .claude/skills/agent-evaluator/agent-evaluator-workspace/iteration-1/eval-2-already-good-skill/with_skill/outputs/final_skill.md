---
name: already-good-skill
description: |
  テストファイル群からバグを検出し、自動評価・改善・レポート生成するスキル。
  
  適用場面：
  - ユーザーが「このテストスイートから潜在バグを検出して」と言ったとき
  - 複数テストが失敗していて、根本原因を調べたいとき
  - テスト駆動開発（TDD）で失敗パターンを分析したいとき
  - 生成レポートの品質を自動評価し、必要に応じて改善したいとき
  
  このスキルは 3 ステップで完全な分析を提供します：実装・テスト・品質評価。
---

# Test Bug Detection & Report Generation Skill

## 目的

テストファイル群から潜在的なバグパターンを検出し、構造化レポートを自動生成・評価するスキル。
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
/detect-test-bugs C:\Projects\MyApp\tests\
```

## 前提条件と入力確認

実行前に以下を確認してください：

### 環境要件

- テストランナーがインストールされている (Jest / pytest / Go test など)
- 対象テストスイートが実行可能な状態（依存関係解決済み）
- テスト結果の標準出力・標準エラーが捕捉可能な環境

### 入力チェック

1. パスが絶対パスまたはリポジトリ相対パスか確認
2. テストファイルが実際に存在するか: `find <path> -name "*.test.*" | head -1`
3. テスト実行権限があるか確認: ファイル数が 0 の場合は早期終了

### サポート対象言語

- **JavaScript / TypeScript**: `.test.js`, `.test.ts`, `.spec.js`, `.spec.ts`
- **Python**: `.test.py`, `_test.py`, `test_*.py`
- **Go**: `*_test.go`
- **その他**: 要カスタマイズ

## スキル構造

このスキルは以下のコンポーネントで構成されます：

```
detect-test-bugs/
├── SKILL.md                    # このファイル
├── scripts/
│   ├── parse_test_output.py    # テスト出力パーサー
│   ├── detect_patterns.py      # バグパターン検出エンジン
│   └── generate_report.py      # レポート生成器
├── references/
│   ├── bug_patterns.json       # 既知バグパターンライブラリ
│   ├── eval_rubric.json        # 評価基準ルーブリック
│   └── LANG_RULES.md           # 言語別テスト規則
└── outputs/                    # 生成レポート出力先
    ├── bug_detection_report.json
    ├── bug_detection_report.md
    └── evaluation_score.txt
```

## ワークフロー

### Phase 1: テストファイル解析

```
1. 入力パス確認: ls <path-to-test-files> で存在確認
2. テストファイル一覧取得: find <path> -type f -name "*.test.*" | wc -l
3. 各テスト実行: <language>-specific test runner (Jest/pytest など)
4. 失敗パターン分類: stdout/stderr をパースし、以下に分類
   - Assertion Failure: 期待値と実際値が異なるケース
   - Timeout: 実行時間が制限時間を超えたケース
   - Setup Error: テストセットアップ失敗
   - Resource Leak: メモリ/ファイルディスクリプタ未開放
5. 共通パターンを検出
```

### Phase 2: バグパターン特定

```
1. エッジケース未処理: 入力境界値（null/undefined/空文字列/0/-1 等）テストの欠落を検査
2. 非決定的テスト（Flaky）: 複数回実行で結果が変わる→タイムスタンプ/ランダム値の依存を検出
3. 依存関係不足: Mock/Stub 定義漏れを検査
4. モック誤用: 期待値設定と実際の呼び出しシーケンスの不整合を検出
```

### Phase 3: レポート生成と品質評価

```
1. 検出されたバグを優先度順にソート
2. 修正提案コードを含めたレポート作成 (JSON / Markdown の 2 形式)
3. テストカバレッジギャップを可視化
4. 生成レポートの品質を評価（下記「評価と改善ループ」参照）
5. スコア < 85点の場合は改善ループを自動実行
```

## 入出力仕様

### 入力

- **path-to-test-files**: テストファイルまたはテストディレクトリへのパス
  - 対応形式: `.test.js`, `.test.ts`, `.spec.py`, `.test.go` など

### 出力

- **Bug Detection Report** (JSON形式): `bug_detection_report.json`
  - 検出されたバグパターン（優先度順）
  - 各バグの深刻度（Critical / High / Medium / Low）
  - 修正提案コード
  - テストカバレッジギャップ分析

- **Bug Detection Report** (Markdown形式): `bug_detection_report.md`
  - 人間が読みやすいフォーマット
  - チェックリスト形式で対応状況を追跡可能

- **評価スコア**: `evaluation_score.txt`
  - 初回スコアと最終スコア
  - 改善の履歴（イテレーション数、各ループの改善幅）

## 評価と改善のワークフロー

生成されたレポートの品質を測定し、必要に応じて改善を繰り返すプロセス。

### スコア評価基準（100点満点）

1. **バグ検出の完全性** (30点)
   - 既知バグがすべて検出されたか
   - False Positive が 5% 以下か
   - 優先度付けが適切か

2. **推奨事項の実用性** (25点)
   - 修正コードが実行可能か
   - 各提案の根拠が明確か
   - ユーザーが容易に実装できるか

3. **レポート形式の完成度** (25点)
   - JSON 出力がスキーマに準拠しているか
   - Markdown が読みやすいか
   - 必要な全項目が含まれているか

4. **テストカバレッジギャップの正確性** (20点)
   - 未テストの分野が正確に識別されているか
   - ギャップ分析の根拠が論理的か

### 改善ループ

```
初回実行 → レポート生成
         ↓
    スコア評価（上記4観点）
         ↓
  スコア < 85 点 ？
    YES → 改善計画立案 → SKILL.md パラメータ調整 → 再実行 → スコア再評価
    NO  → 完了、ユーザーに報告
```

### 改善報告書テンプレート

各ループ後、以下形式で改善内容を記録：

```markdown
## Iteration N 改善報告

### スコア推移
- 初回スコア: XX/100
- 改善後スコア: YY/100
- 改善幅: +Z点

### 実施した改善
1. [改善内容]: [詳細]
2. ...

### 次のステップ
- スコア 85点以上なら完了
- スコア未達なら [次改善項目] を優先

### 生成ファイル
- bug_detection_report.json: <file-size>
- bug_detection_report.md: <file-size>
- evaluation_score.txt: <content>
```

## 完了条件

以下をすべて満たした場合、タスク完了：

- [ ] Bug Detection Report (JSON形式) が生成されている
- [ ] Bug Detection Report (Markdown形式) が生成されている
- [ ] 各バグが「優先度」「深刻度」「修正提案」を含んでいる
- [ ] テストカバレッジギャップ分析が完了している
- [ ] 評価スコアが記録されている
- [ ] スコア < 85点の場合、改善ループが実行された
- [ ] 最終スコアが初回と比較で記録されている

## 出力ファイル確認

生成ファイルをチェック：

```bash
# JSON レポート
cat <output-dir>/bug_detection_report.json

# Markdown レポート
cat <output-dir>/bug_detection_report.md

# スコア履歴
cat <output-dir>/evaluation_score.txt
```

最終スコアが 85 点以上なら完了。未満なら改善ループを繰り返す。

## プロジェクト統合ガイド

このスキルは Kyosist プロジェクトの以下ルール・スキルと連携：

### 参考にすべきルール

- `.claude/rules/pdca-workflow.md` — Check フェーズでコード品質を評価する際に参考
- `.claude/rules/coding-standards.md` — テストが言語別の品質規約に準拠しているか検証
- `.claude/rules/error-recovery.md` — 失敗したテストの原因分析・再試行ルール

### 連携スキル

- `pdca-check-reviewer` — 生成レポートを超厳格にレビュー（最終品質確保）
- `senior-code-reviewer` — 修正提案コードの妥当性検証

### 実装例（PDCA ワークフロー）

```
1. 開発者: /detect-test-bugs ./src/api/ を実行
2. 本スキル: バグ検出 → スコア評価 (78点) → 改善提案
3. 開発者: 修正を実装
4. 開発者: /pdca スキルで Check フェーズ実施
5. pdca-check-reviewer: 生成レポートを検証 → CHECK OK
6. マージ実行
```

## トラブルシューティング

### テストファイルが見つからない場合

```
Error: No test files found in the specified directory.
Supported patterns: *.test.js, *.test.ts, *.spec.py, *.test.go
```

**確認事項：**
- パスが正しいか確認: `ls <path>`
- テストファイルが標準的な命名規則に従っているか
- ディレクトリ権限があるか確認

### バグが検出されない場合

**症状**: Bug Detection Report にバグが列挙されていない

**確認手順:**
1. テストが実行されたか確認: `<test-runner> <path> --verbose`
2. テスト実行結果がパーサーで正しく読み込まれているか確認
3. 既知バグパターンライブラリ (bug_patterns.json) が最新か確認
4. テストカバレッジが 100% に近い場合、設計上のバグ（論理バグ）を追加分析

**解決策:**
- テスト改善後、再度本スキルを実行
- 既知パターンに該当しないバグ型の場合は、`bug_patterns.json` をカスタマイズ

### スコア改善が停滞する場合

**症状**: 複数ループを経ても スコア 85点に到達しない

**対処:**
1. 改善対象項目が正しく特定されているか確認
2. 評価基準（eval_rubric.json）が現在のテスト内容に合致しているか再検討
3. ユーザーに相談し、スコア基準を調整するか、現在の品質で運用するかを判断

## 制限事項

- 実行されたテスト出力の分析に依存（静的解析ではない）
- ランタイムエラーのみを検出（論理バグは部分的）
- テストが実行可能な状態である必要がある
- テストカバレッジギャップ分析は、テストコードの可視性に依存

## よくある質問

### Q1. 複数言語のテストスイートに対応していますか？

**A**: はい。JavaScript/TypeScript、Python、Go をネイティブ対応。
その他言語の場合は、テスト出力フォーマットが標準的（stdout/stderr のアサーション失敗表記）であれば対応可能。
カスタム言語の場合は LANG_RULES.md を拡張してください。

### Q2. 修正提案は実装まで含みますか？

**A**: 修正提案コードを含みますが、実装は開発者が実施。
提案コードは「コピペで動作する」レベルが目標です。

### Q3. 本スキル生成のレポート自体の品質を保証できますか？

**A**: はい。本スキル自体が、生成レポートを4観点で自動評価し、スコア < 85点の場合は改善を繰り返します。
最終レポート品質は 85点以上を保証します。

### Q4. スコア 85点未満の場合は何が起こりますか？

**A**: 自動的に改善ループが実行され、以下が実施されます：
1. 低スコア箇所を特定
2. パラメータ・ルール調整
3. レポート再生成
4. スコア再評価

ユーザー操作は不要です。

### Q5. 改善ループは何回まで繰り返されますか？

**A**: デフォルトでは無制限。ただし、2ループ連続で改善幅が 3点未満の場合は停滞と判定し、ユーザーに確認します。

## 成功例

### 例1: 非決定的テスト検出

```
Input: ./tests/async/
Output:
- 🔴 Critical: Race condition in timeout handler
  Suggestion: Add proper await/barrier
- 🟡 High: Flaky date-based test
  Suggestion: Use frozen time (e.g., jest.useFakeTimers)

初回スコア: 68/100
改善1: タイムアウト検出ロジック改善
改善後スコア: 82/100
改善2: 日時依存テスト検出を強化
最終スコア: 87/100 ✓完了
```

### 例2: エッジケース検出

```
Input: ./spec/auth.test.ts
Output:
- Coverage gap: null/undefined inputs not tested
- Coverage gap: UTF-8 special characters in email validation
- Suggestion: Add test cases for these scenarios

初回スコア: 74/100
改善1: エッジケース検出ルール拡張
最終スコア: 86/100 ✓完了
```
