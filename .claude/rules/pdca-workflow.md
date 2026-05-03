---
globs: ["**/*"]
---

# 実装ワークフロー（PDCA サイクル）

すべての実装・修正タスクにこのワークフローを適用する。
**オーケストレーターは自身で作業せず、すべてを専門サブエージェントへ委譲する。**

## サイクル概要

```
Plan → Do → PR作成 → Check → (NG: Do へ戻る) → (OK: マージ)
```

---

## Phase 1: Plan（tech-lead-researcher）

- タスクの要件整理・技術選定・WBS化
- 実装前に曖昧点があれば最大3問まで確認を求める
- 出力: アーキテクチャ方針 + タスク分割

## Phase 2: Do（frontend-ui-specialist / backend-specialist）

- Plan の成果物に基づき実装
- フロントエンド変更 → `frontend-ui-specialist`
- バックエンド変更 → `backend-specialist`
- 両方変更 → それぞれ並列実行
- 実装後、git-push スキルで **GitHub に PR を作成する**

## Phase 3: Check（senior-code-reviewer）

- **Do と必ず別エージェント**（Gen/Eval 分離、自己評価バイアスを排除）
- レビューは **一回限り・超厳格・遠慮なし** で全指摘を一度に洗い出す
- 必ず PlaywrightCLI（`my-playwright-project/`）で画面の動作確認を行う
  ```bash
  cd my-playwright-project && npx playwright test --headed
  ```
- コンテキスト汚染を最小化するため、Diff の見渡しのみ行う（ファイル全読み込みしない）
- **レビュー通過**: そのままマージまで実行
- **レビュー非通過**: 全修正点を一覧化して Do へ差し戻し

## Phase 4: Act（Do 差し戻し時）

- Check から戻った修正点を **TaskCreate で TODO 化・細分化する**
- 1つ完了 → TaskUpdate で完了マーク → 次へ（逐次消化）
- 全修正完了後、再度 PR を作成して Check へ戻る
- レビューが通るまで Do → Check サイクルを繰り返す

---

## Playwright 設定

- プロジェクト: `my-playwright-project/`
- baseURL: `http://localhost:8000`（`run.py` でサーバーを起動してからテスト実行）
- テスト実行: `cd my-playwright-project && npx playwright test`
- 新テスト追加場所: `my-playwright-project/tests/`

---

## ワークフロー上の禁止事項

- オーケストレーター自身がコードを書く・編集する（委譲のみ）
- Do と Check を同一エージェントに担わせる
- Check で一部の指摘を後回しにする（一回で全件洗い出し）
- PR 作成なしに直接 main ブランチへコミットする
