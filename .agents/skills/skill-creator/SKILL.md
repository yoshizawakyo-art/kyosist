---
name: skill-creator
description: Codex向けスキルを新規作成・改善・評価するためのワークフロー。ユーザーが「スキルを作りたい」「既存スキルを改善したい」「評価を回したい」「発火しやすいdescriptionに最適化したい」と依頼したときに使う。
---

# Codex Skill Creator

Codexで使うスキルを設計し、評価し、改善するための実践ガイド。

## Goal

このスキルの目的は次の3つ:
- 新規スキルを短時間で動く形まで作る
- 評価ループ（定性 + 定量）で品質を上げる
- `description` を最適化して適切に発火させる

## Workflow

1. 目的と成功条件を確定する
2. `SKILL.md` 初稿を作る
3. 2〜3件の実運用に近い eval prompt を作る
4. with-skill / baseline を同時実行して比較する
5. assertion を作成・採点・集計する
6. ベンチマーク結果とユーザーフィードバックで改稿する
7. 必要なら description 最適化を実行する

## 1) Intent Capture

最初に以下を埋める:
- 何を自動化したいか
- どんなユーザー発話で発火させたいか
- 出力形式（例: パッチ、要約、JSON、チェックリスト）
- 成功判定（何ができればOKか）

既存会話に材料がある場合はそこから抽出し、足りない点だけ追加で質問する。

## 2) SKILL.md Authoring Rules

- Frontmatter の `name` と `description` は必須
- 「いつ使うか」は `description` に明示する
- 本文は手順を命令形で簡潔に書く
- 500行を超えそうなら `references/` に分割する
- 分岐がある場合は「どの条件でどのファイルを読むか」を明記する

推奨構成:

```text
<skill>/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

## 3) Eval Prompt Design

`evals/evals.json` を作り、まずは prompt 中心で定義する。

```json
{
  "skill_name": "skill-creator",
  "evals": [
    {
      "id": 1,
      "prompt": "実際のユーザー依頼に近い文",
      "expected_output": "期待される結果の説明",
      "files": []
    }
  ]
}
```

主観評価が中心のスキルなら定量 assertion は最小限でよい。

## 4) Run Strategy (Codex)

各 eval ごとに次を同一ターンで起動する:
- with-skill: 新スキルあり
- baseline: 新規作成時はスキルなし、改善時は旧版スキル

出力先:

```text
<skill>-workspace/
  iteration-1/
    <eval-name>/
      with_skill/outputs/
      without_skill/outputs/   (または old_skill/outputs/)
```

`eval_metadata.json` も各 eval ディレクトリに保存する。

## 5) While Running

実行待ちの間に assertion を作る。assertion は「自動判定できるか」を優先する。

`eval_metadata.json` 例:

```json
{
  "eval_id": 0,
  "eval_name": "create-minimum-skill",
  "prompt": "...",
  "assertions": []
}
```

## 6) Grading and Aggregation

1. 各 run の `grading.json` を作成
2. 集計スクリプトを実行

```bash
python3 -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
```

3. 生成物を確認
- `benchmark.json`
- `benchmark.md`

`grading.json` の expectations は必ず以下キー名を使う:
- `text`
- `passed`
- `evidence`

## 7) Review Viewer

レビュー画面を生成:

```bash
python3 eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "<name>" \
  --benchmark <workspace>/iteration-N/benchmark.json
```

GUIが使えない環境では `--static <output.html>` を使う。

## 8) Iteration Rules

- 1イテレーションごとに「変更点」「改善した根拠」「次の仮説」を残す
- 改善が見られない assertion は削除または再設計する
- variance が大きい eval は flaky とみなし、分割または判定を単純化する

## 9) Description Optimization

description は次を必ず含める:
- 何をするスキルか
- どんな依頼文で呼ぶべきか
- 呼ばれた結果として何が返るか

必要なら `scripts/improve_description.py` を使って候補を生成し、人手で最終調整する。

## 10) Safety

- 不正アクセス・マルウェア・権限逸脱を目的とするスキルは作成しない
- ユーザー意図を偽装する設計（隠し挙動、秘密送信など）を入れない
- 実行時に破壊的コマンドが必要な場合は明示的に確認する

## Bundled Files

このスキルは以下の補助ファイルを利用する:
- `scripts/` : 評価・集計ユーティリティ
- `references/schemas.md` : eval/benchmark スキーマ
- `agents/` : grader / analyzer / comparator の補助ガイド
- `eval-viewer/` : レビュー画面生成

必要なファイルだけ読み込み、全ファイルを一括で展開しないこと。
