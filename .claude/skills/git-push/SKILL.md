---
name: git-push
description: |
  GitHubへのコード変更プッシュのフルワークフロー。
  「コミットして」「プッシュして」「GitHubに上げて」「PRを作って」「変更を保存して」「ブランチ切って」などのフレーズで必ず使う。
  変更確認 → ブランチ作成 → ステージング → コミットメッセージ生成 → コミット → プッシュ → PR作成 の一連の流れをすべてカバーする。
  git操作が絡む作業ならこのスキルを積極的に使うこと。
---

# git-push: GitHub プッシュ ワークフロー

git 操作全般を安全・確実に実行するスキル。以下のフェーズを順に実行する。

---

## フェーズ 1: 現状把握

作業開始前に必ず以下をパラレルで実行し、状況を把握する:

```bash
git status
git diff
git log --oneline -10
git branch -a
```

把握すべき情報:
- **現在のブランチ名**
- **未コミット変更の一覧**（M: 変更済み、??: 未追跡）
- **ステージ済みファイル**
- **リモートとの差分**（ahead/behind）

---

## フェーズ 2: ブランチ管理

### ケース別の対応

**A. main/master に直接コミットする場合**
- 軽微な修正・ドキュメント更新のみ可
- それ以外は必ずブランチを切るようユーザーに提案する

**B. 新しいブランチを作る場合**

ブランチ命名規則:
```
feature/<short-description>   # 機能追加
fix/<short-description>        # バグ修正
docs/<short-description>       # ドキュメント
chore/<short-description>      # 雑務・設定変更
refactor/<short-description>   # リファクタリング
```

例: `feature/agent-step-logging`, `fix/chat-message-scroll`

```bash
git checkout -b feature/<name>
```

**C. 既存ブランチに追加する場合**
```bash
git checkout <branch-name>
```

---

## フェーズ 3: ファイルのステージング

### 安全チェック

以下のファイルは**絶対にステージしない**:
- `.env`, `.env.*`, `*.env`（シークレット・APIキー）
- `*.pem`, `*.key`, `*.p12`（証明書・秘密鍵）
- `__pycache__/`, `*.pyc`
- `node_modules/`
- ビルド成果物（`dist/`, `build/`, `.vercel/`）

上記ファイルが変更リストに含まれている場合、ユーザーに警告してステージを省略する。

### ステージング方法

原則: **`git add .` や `git add -A` は使わない**。ファイル名を明示してステージする。

```bash
git add src/api/index.py src/public/chat/main.js
```

ユーザーがステージ対象を指定していない場合、変更ファイルの一覧を見せて確認を取る。

---

## フェーズ 4: コミットメッセージ生成

### フォーマット

```
<type>: <subject>

[body - 任意: 変更の背景・理由]
[footer - 任意: breaking changes, closes #issue]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

**type の選択肢:**

| type | 使う場面 |
|------|---------|
| `feat` | 新機能の追加 |
| `fix` | バグ修正 |
| `docs` | ドキュメントのみの変更 |
| `style` | コードの意味に影響しない変更（フォーマット等） |
| `refactor` | バグ修正でも機能追加でもないコード変更 |
| `test` | テストの追加・修正 |
| `chore` | ビルドプロセスや補助ツールの変更 |
| `perf` | パフォーマンス改善 |

### メッセージ生成の考え方

- `subject` は **何をした** ではなく **何が変わったか** を動詞で書く（英語 or 日本語）
- `body` には **なぜその変更が必要だったか** を書く（what は diff で分かる）
- 過去の commit log のスタイル（`git log --oneline -10` の結果）に合わせる

**良い例:**
```
feat: エージェント実行ステップをDBに記録する機能を追加

チャットUI側でストリーミング進捗を表示するため、
agent_stepsテーブルへのINSERT処理をagent_service.pyに実装。
```

**悪い例:**
```
update files  # 何をしたか不明
fix bug       # どのバグか不明
```

### ユーザーへの確認

メッセージ案をユーザーに提示し、承認を得てからコミットする:

```
以下のコミットメッセージでよいですか？

---
feat: エージェント実行ステップをDBに記録する機能を追加

チャットUI側でストリーミング進捗を表示するため、
agent_stepsテーブルへのINSERT処理をagent_service.pyに実装。

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
---
```

---

## フェーズ 5: コミット実行

承認を得たら HEREDOC 形式でコミット:

```bash
git commit -m "$(cat <<'EOF'
feat: エージェント実行ステップをDBに記録する機能を追加

チャットUI側でストリーミング進捗を表示するため、
agent_stepsテーブルへのINSERT処理をagent_service.pyに実装。

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

pre-commit フックが失敗した場合:
1. エラー内容を確認する
2. 原因（ruff エラー等）を修正する
3. 修正ファイルを再ステージして **新しいコミット**を作る（`--amend` 禁止）

---

## フェーズ 6: プッシュ

### push 前の確認（必須）

push は **元に戻せない公開操作**のため、以下を必ずユーザーに確認する:

```
以下の push を実行してよいですか？

  ブランチ: feature/agent-step-logging
  リモート: origin
  コミット: 1件
    - feat: エージェント実行ステップをDBに記録する機能を追加
```

### push コマンド

**通常の push:**
```bash
git push origin <branch-name>
```

**初回 push（リモート追跡ブランチなし）:**
```bash
git push -u origin <branch-name>
```

### 禁止操作

以下は安全プロトコル上 **絶対に実行しない**:
- `git push --force` / `git push -f`（`--force-with-lease` は許可）
- main/master への直接 push（PR フロー必須）

---

## フェーズ 7: PR 作成（任意）

ユーザーが PR 作成を求めた場合、または feature/fix ブランチを push した場合は PR 作成を提案する。

### PR の構成

```bash
gh pr create --title "<PRタイトル>" --body "$(cat <<'EOF'
## Summary
- <変更点1>
- <変更点2>

## Test plan
- [ ] ローカルで動作確認済み
- [ ] ruff check 通過済み

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### PR タイトルの命名

コミットメッセージの subject をそのまま使うか、複数コミットの場合は変更の全体像を要約する。
70文字以内に収める。

---

## Safety プロトコル

### 危険操作への対応

以下に該当する場合は `.claude/rules/safety.md` の警告フォーマットに従いユーザー承認を必ず取得:
- `git reset --hard`
- `git push --force`
- `git branch -D`（ブランチ削除）
- main/master ブランチへの直接 push

### 作業スコープ

このスキルが自律的に進めてよい操作:
- ファイルのステージング・アンステージ
- コミット（ユーザー承認後）
- ブランチ作成・切り替え

必ずユーザー確認が必要な操作:
- `git push`（いかなる場合も）
- PR の作成・クローズ
- ブランチの削除
