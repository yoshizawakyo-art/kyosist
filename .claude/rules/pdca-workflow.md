---
globs: ["**/*"]
---

# 実装ワークフロー（PDCA サイクル）

すべての実装・修正タスクにこのワークフローを適用する。

## サイクル概要

```
通常フロー:
  Plan → Do → Check → PR作成 → PR最終レビュー → (指摘あり: 修正→直接push→再レビュー) → (OK: マージ)

軽微修正フロー（1〜5行・設定ファイルのみ）:
  Do → Check → PR作成 → PR最終レビュー → (指摘あり: 修正→直接push→再レビュー) → (OK: マージ)
  ※ Playwright は省略可（UI変更を伴わない修正のみ）
```

**変更の規模にかかわらず、Check・PR作成・PR最終レビュー・マージは必ずこの順で実施する。**

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
- **PR作成はこのフェーズでは行わない**（Checkを通過してから行う）

## Phase 3: Check（senior-code-reviewer）

- **Do と必ず別エージェント**（Gen/Eval 分離、自己評価バイアスを排除）
- レビューは **一回限り・超厳格・遠慮なし** で全指摘を一度に洗い出す
- 必ず PlaywrightCLI（`my-playwright-project/`）で画面の動作確認を行う
  ```bash
  cd my-playwright-project && npx playwright test --headed
  ```
  （Playwright省略条件: `.json`/`.md`/`.toml` 等の設定・ドキュメントのみ、またはUI非影響のサーバー変更のみ）
- コンテキスト汚染を最小化するため、Diff の見渡しのみ行う（ファイル全読み込みしない）
- **レビュー通過 → Phase 4（PR作成）へ進む**
- **レビュー非通過 → 全修正点を一覧化して Do へ差し戻し**

## Phase 4: PR作成（git-push スキル）

- Check 通過後、`git-push` スキルで GitHub に PR を作成する
- PR タイトル・本文は変更内容を簡潔に記述する
- **PR作成後、すぐに Phase 5（PR最終レビュー）へ進む**

## Phase 5: PR最終レビュー（/review スキル）

- `/review` スキルで GitHub PR をレビューする
- レビュー観点: PR説明の正確さ、変更範囲の妥当性、未解決の指摘がないか
- **レビュー通過（指摘なし）→ ユーザー確認不要でマージまで実行**
  ```bash
  gh pr merge --merge --auto
  ```
- **指摘あり → Phase 6（修正・直接push）へ**

## Phase 6: Act（PR最終レビュー差し戻し時）

- 指摘事項を **TaskCreate で TODO 化・細分化する**
- 1つ完了 → TaskUpdate で完了マーク → 次へ（逐次消化）
- 修正後は **新規PRを作らず、同じブランチに直接 push する**（PRは自動更新される）
  ```bash
  git add <files>
  git commit -m "fix: <修正内容>"
  git push
  ```
- push 完了後、**Phase 5（PR最終レビュー）に戻る**
- レビューが通るまで 修正→push→レビュー サイクルを繰り返す

---

## Playwright 設定

- プロジェクト: `my-playwright-project/`
- baseURL: `http://localhost:8000`（`run.py` でサーバーを起動してからテスト実行）
- テスト実行: `cd my-playwright-project && npx playwright test`
- 新テスト追加場所: `my-playwright-project/tests/`

---

## ワークフロー上の禁止事項

- Do と Check を同一エージェントに担わせる
- Check で一部の指摘を後回しにする（一回で全件洗い出し）
- Check を経ずに PR を作成する
- PR最終レビューを経ずにマージする
- PR最終レビューの指摘修正後に新規PRを作成する（直接pushで同PRを更新する）
- **Check を経ずにタスク完了を宣言する（規模・行数・ファイル種別に関わらず禁止）**
- **PR最終レビュー通過前にマージする**
