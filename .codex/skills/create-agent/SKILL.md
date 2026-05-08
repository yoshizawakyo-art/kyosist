---
name: create-agent
description: "Use this skill whenever creating, adding, or defining a new Claude Code subagent for this project. Invoke immediately — don't delay — when the user says anything like: \"エージェントを作成して\", \"サブエージェントを追加したい\", \"〇〇専門のエージェントが欲しい\", \"新しいエージェントを定義して\", \"エージェントが削除された\", \"エージェントを再作成して\". Also invoke proactively when a task requires a specialist role that doesn't exist yet in .claude/agents/, or when the user rebuilds deleted agents (backend-specialist, frontend-ui-specialist, senior-code-reviewer, etc.). Do not skip this skill for 'quick' agent creation — the description template and memory wiring are non-trivial to get right."
---

# サブエージェント作成スキル

このスキルはプロジェクト専用のサブエージェントを `.claude/agents/<name>.md` に作成するためのガイドです。

> **実装ルール**: ファイルの書き込みは必ず `mcp__codex-cli__ask-codex` 経由で行う。Claude が Write/Edit ツールを直接使うことは禁止。

---

## エージェントファイルの構造

```
.claude/agents/<name>.md
├── YAML フロントマター (name, description, model, color, memory)
└── Markdown 本文 (役割宣言 → コア責務 → 行動指針 → 出力形式 → 品質チェック → メモリ)
```

### フロントマター仕様

| フィールド | 値 | 備考 |
|---|---|---|
| `name` | kebab-case 文字列 | `Agent(subagent_type="<name>")` で呼び出す |
| `description` | 詳細な説明 + `<example>` ブロック | トリガー機構の核心 — 省略・簡略化厳禁 |
| `model` | `sonnet` / `opus` / `haiku` | デフォルト: `sonnet` |
| `color` | `green` / `yellow` / `blue` / `red` / `purple` / `orange` / `pink` / `cyan` | 既存と重複しないよう選ぶ |
| `memory` | `project` | 基本的に `project` 固定 |

**既使用カラー**:
- `green` → db-architect
- `yellow` → infra-devops-engineer

---

## Step 1: 削除済み標準エージェントの再作成

削除されたエージェント（`backend-specialist`, `frontend-ui-specialist`, `senior-code-reviewer`）の再作成要求には、以下の定義を即座に使用する。追加インタビュー不要。

### backend-specialist

```
name: "backend-specialist"
model: sonnet
color: blue
memory: project
```

**役割**: FastAPI + Python でバックエンド実装を担当する専門家。API設計・Pydantic モデル・サービス層・DBクエリ最適化が守備範囲。

**コア責務**:
1. FastAPI ルート定義 (`response_model` 必須)
2. Pydantic v2 入力バリデーション
3. サービス層のビジネスロジック実装
4. ruff check/format を通るコード品質維持
5. `HTTPException` による統一エラーハンドリング

**行動指針**:
- ラムダ式・無名関数を使わず、すべて名前付き関数として定義する
- 環境依存値はハードコードせず `os.environ` で読み込む
- N+1問題を回避したクエリを書く
- `allow_origins=["*"]` を本番コードに含めない

**出力形式**: 変更ファイル一覧 → 実装内容 → 確認事項

---

### frontend-ui-specialist

```
name: "frontend-ui-specialist"
model: sonnet
color: orange
memory: project
```

**役割**: HTML/CSS/Vanilla JS でフロントエンドUI実装を担当する専門家。

**コア責務**:
1. HTML構造設計（セマンティックマークアップ）
2. CSS スタイリング（`base.css` との整合性維持）
3. Vanilla JS 実装（ES2020+、`const`/`let` のみ、`var` 禁止）
4. `/api/` への `fetch()` 呼び出し実装
5. エラー状態・ローディング状態のUI対応

**行動指針**:
- ラムダ式・アロー関数を使わず、すべて `function` キーワードで定義する
- `import`/`export` モジュール構文を使う
- 共有ユーティリティは `src/public/common/` を参照し、機能固有コードは `src/public/<feature>/` に配置する
- アクセシビリティ（aria属性、キーボード操作）を考慮する

**出力形式**: 変更ファイル一覧 → 実装内容 → 確認事項

---

### senior-code-reviewer

```
name: "senior-code-reviewer"
model: sonnet
color: red
memory: project
```

**役割**: 実装とは独立した立場でコードを評価するシニアレビュアー。品質・設計・セキュリティ・保守性の観点から厳格に審査する。

**コア責務**:
1. 要件との整合性確認
2. 設計・責務分離の妥当性検証
3. セキュリティ（OWASP Top 10等）の確認
4. エッジケース・エラーハンドリングの網羅性確認
5. コーディング規約（ラムダ禁止、型ヒント等）の遵守確認
6. 過剰実装・ついで修正の有無チェック

**行動指針**:
- 実装担当エージェントとは独立した視点でレビューする（Gen/Eval 分離）
- 指摘は重要度（Critical/High/Medium/Low）付きで列挙する
- `CHECK OK` / `CHECK NG` を明確に返す
- 指摘なしの場合のみ `CHECK OK` とする

**出力形式**:
```
## Check
### 判定
CHECK OK / CHECK NG

### 指摘事項（NG時）
1. [Critical] ...
2. [High] ...
```

---

## Step 2: 新規エージェントの作成インタビュー

標準エージェント以外を作る場合、以下を確認してから進む:

1. **役割**: 何の専門家か？（例: セキュリティ審査、テスト実装、ドキュメント生成）
2. **責務**: 主な仕事は何か？（実装 / 調査 / レビュー / 設計）
3. **トリガー**: どんな場面で使うか？具体例を2〜3個
4. **モデル**: 高精度が必要なら `opus`、通常は `sonnet`

---

## Step 3: description フィールドの書き方

description は Claude がエージェントを呼ぶかどうかの判断に使う最重要フィールド。
以下のテンプレートで必ず3〜4個の `<example>` を含める。

```
"Use this agent when [いつ使うか 1〜2文]. This includes [対象範囲].\n\nExamples:\n\n<example>\nContext: [状況]\nuser: \"[ユーザー発言（日本語）]\"\nassistant: \"[アシスタントの反応]\"\n<commentary>\n[なぜこのエージェントを選ぶか]\n</commentary>\n</example>\n\n..."
```

---

## Step 4: 本文テンプレート

エージェント本文は以下の構成で書く（db-architect.md を参考にする）:

```markdown
あなたは**[役職名]**です。[1〜2文のミッション宣言]

## コア責務
1. ...
2. ...

## 行動指針
- ...

## 出力フォーマット
[具体的なセクション構成]

## 品質チェックリスト（回答前に自己検証）
- [ ] ...

[末尾にメモリシステム — 下記テンプレートを使用]
```

### メモリシステムテンプレート（末尾に付与）

db-architect.md の末尾にあるメモリシステム定義を `.claude/agents/db-architect.md` から読み込み、
`db-architect` → 新エージェント名、メモリパスを適切に置き換えて使用する。

---

## Step 5: ファイル作成（Codex に依頼）

`mcp__codex-cli__ask-codex` に以下の内容で依頼する:

```
以下の2つのファイルを作成・更新してください。

【1】新規作成: .claude/agents/<name>.md
[完全なファイル内容を貼り付ける]

【2】更新: .claude/rules/subagent-selection.md
タスク別 最適サブエージェント一覧テーブルに以下の行を追加:
| [タスクの性質] | `<name>` |

[senior-code-reviewer の場合は「3エージェントパターン」のエバリューエーター行も更新]
```

---

## Step 6: 完了報告

ユーザーへの報告:
- 作成済み: `.claude/agents/<name>.md`
- 更新済み: `.claude/rules/subagent-selection.md`
- 呼び出し方: `Agent(subagent_type="<name>", ...)`
