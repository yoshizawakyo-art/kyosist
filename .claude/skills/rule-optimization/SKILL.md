---
name: rule-optimization
description: Codex の workflow miss（「Check を忘れた」「不要な処理が混ざった」）や user feedback（「ルール化しよう」「スキル化して」）を root cause 分析して、AGENTS.md / CLAUDE.md / .claude/rules / .claude/skills に反映可能な durable rule に変換する。Step 1 で miss パターンを、Step 2 の判定テーブルで home ファイルを、Step 3 で実装・検証を、Step 4 で ledger 記録を実施。
---

# Rule Optimization

Use this skill to convert a concrete workflow miss into a small, enforceable rule change. Optimize the rule system, not the last answer.

## Workflow

1. Identify the missed behavior.
   - State the exact action that was forgotten or done late.
   - Identify when it should have happened.
   - Keep the fix procedural and observable.

2. Choose the durable home.

| Miss / Feedback | Root Cause | Home | 判定フロー |
|---|---|---|---|
| Codex が禁止事項を繰り返す（e.g., ラムダ式、`allow_origins=["*"]`） | Coding rule not enforced | `CLAUDE.md` > `.claude/rules/coding-standards.md` | coding-standards に具体禁止例を追加。重複なければ CLAUDE.md に追記。 |
| PDCA Check NG が 2 回以上繰り返される | Workflow gate missing | `.claude/rules/pdca-workflow.md` | pdca-workflow の appropriate phase に verification gate / checklist を追加。 |
| ワークフロー手順が見落とされる（e.g., PR作成前に Check 走らせ忘れ） | Procedural ambiguity | `.claude/rules/pdca-workflow.md` | pdca-workflow.md に「Step N の完了条件」として明示的な gate を追加。 |
| Codex がスコープ外の修正を混ぜる、過剰な一般化を入れる | Do/Act ガイドが曖昧 | `CLAUDE.md` > `.claude/rules/pdca-workflow.md` | CLAUDE.md の "Behavioral Rules" か pdca-workflow.md の "Phase 2/6" に overreach 防止を追記。 |
| エージェント選択が誤る（e.g., 実装を backend-specialist に丸投げ） | Subagent rule unclear | `.claude/rules/subagent-selection.md` | subagent-selection の判定表にタスク型を追加、または「禁止」明示。 |
| Codex MCP ツール失敗（e.g., `ask-codex` --full-auto エラー） | Tool failure pattern unknown | `.claude/rules/error-recovery.md` | error-recovery の「既知のワークアラウンド」に tool name, error signature, workaround を記録。 |
| ルール更新で Codex / Claude 側が矛盾する | Rule drift | 変更対象 + 逆側確認 | 一つ側を直したら、逆側（AGENTS.md 側なら CLAUDE.md 側も、またはスキル側も）の対応ファイルを confirm して、同一ターン内で同期更新。 |
| 将来再利用可能な domain workflow を形成化 | Repeated pattern across sessions | 新 skill: `.claude/skills/<domain>/SKILL.md` | trigger, steps, validation, report を明記した新スキルファイルを作成。CLAUDE.md か AGENTS.md に「このスキル使用時」の reference を追記。 |

   **判定ロジック**:
   - まず root cause を Step 1 で特定する。
   - 次に表左側の「Miss / Feedback」に該当する行を探す。
   - その行の「Home」欄が更新対象ファイル。複数ある場合は優先順。
   - 判定フローに沿って、具体的な編集位置と変更内容を確定。

3. Patch the smallest useful rule.
   - Add a checklist/gate at the phase where the miss occurred.
   - Prefer "before final response, verify X" over broad reminders.
   - Include what to record, where to record it, and what blocks completion.
   - **実装タイミング判定**: 以下を確認して、単一ファイル更新か複数ファイル同時更新かを判定する。
     - Step 1 で特定した root cause が単一テーマか、複数テーマが混在しているか
     - 判定テーブル（Step 2）で「Home」に複数ファイルが挙げられているか
     - `いいえ` → 単一ファイル集中編集（修正漏れなし）
     - `はい` → 複数ファイル同時更新。Step 3 で「両側確認」を必ず実施。Codex / Claude の逆側ファイルも同時チェック。
   - When adding or changing a skill or rule, check both Codex-facing files and `.claude` counterparts in the same turn.
   - Mirror behavior, not necessarily file format: keep trigger intent, required gates, validation, and ledger rules consistent.
   - If the user asks to make the rule automatic or hook-based, add or update a hook under `.claude/hooks/` and register it in `.claude/settings.local.json` or `.claude/settings.json` as appropriate.
   - For session-continuity automation, prefer hooks that write Markdown handoff files under `.claude/doc/session-handoffs/` and keep a `latest-session-handoff.md` copy.
   - Avoid duplicating the same paragraph in many files; use short pointers when possible.

4. Update the task ledger.
   - If `.claude/doc/pending-tasks.md` exists, add the rule optimization under completed work.
   - Mark completed items with `[x]`.
   - Leave unresolved follow-ups as `[ ]` with a reason.
   - Record whether `.claude` counterparts were updated, already aligned, or intentionally not changed.
   - If the ledger is ignored by git, still update it locally and mention that in the final report.

5. Validate.
   - Run `git diff --check` on changed tracked rule files.
   - Validate hook JSON with a parser, for example `python3 -m json.tool .claude/settings.local.json`.
   - Test hook scripts with representative stdin when practical.
   - If a hook depends on optional runtime metadata, test both a positive payload and the no-metadata no-op path.
   - For Codex skill changes, run:
     `python3 /home/yoshizawa/.codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>`
   - Review the diff for overreach: rule changes should be narrower than the incident.

## Check Phase: 検出対象の具体パターン

rule-optimization が対象にする workflow miss の具体例を示します。これらの miss を検出したら、Step 1 で root cause を分析し、判定フロー（Step 2）に従ってルール化します。

### 検出対象パターン

1. **見落とされた検証ステップ**
   - 症状: PR が Check フェーズをスキップして作成された。Code review で指摘されても同じ miss が繰り返される。
   - パターン例: pdca-workflow.md の "Phase 3: Check" の実施条件が曖昧、または DoD に Check 実施が記載されていない。
   - 対応: pdca-workflow.md の appropriate phase に「Check 未完了では次フェーズに進まない」を明示。

2. **重複する条件分岐**
   - 症状: Codex が同一ファイル内で矛盾する複数フォーマット規則を適用。複数ツール（ruff と oxlint 等）の設定が衝突。
   - パターン例: coding-standards.md で「コードフォーマットは Ruff」と定義されているのに、スキルでは Oxlint 使用を指示。
   - 対応: coding-standards.md に「1 プロジェクト 1 フォーマッタ」の原則を追加。矛盾する場合は AGENTS.md / CLAUDE.md の優先順序を明記。

3. **不要な待機処理が混ざる**
   - 症状: `time.sleep()` や `sleep 10` がテスト / ポーリングロジックに混ざる。本番コードに誤ってデバッグ待機が残される。
   - パターン例: operations.md に「polling は Monitor ツール使用」と書かれているのに、bash スクリプトで sleep ループが実装される。
   - 対応: error-recovery.md に「sleep 使用禁止のシナリオ」をリスト化、または operations.md に polling ガイドを強化。

4. **スコープ外の修正が混ざる**
   - 症状: Issue で「A を修正」と指定したのに、実装で「A + 関連する B, C も修正」が含まれる。PR diff が予想より大きくなり、レビュー混乱。
   - パターン例: pdca-workflow.md Phase 2 Do で「過剰実装禁止」は書かれているが、「ついで修正をどう判定するか」が曖昧。
   - 対応: pdca-workflow.md に「過剰実装の判定例」を追加。「別タスク化」の手順を明記。

5. **エージェント選択ミス**
   - 症状: Claude が backend-specialist を実装担当に使うことがあり、pdca-workflow.md の禁止ルール（「実装は Codex のみ」）を繰り返す。
   - パターン例: subagent-selection.md に実装担当の禁止明記がないまま、一般化した「タスク分類」だけがある。
   - 対応: subagent-selection.md に「実装担当禁止」を明示。違反した場合の対応フロー（error-recovery.md に記載）を参照。

6. **ルール同期漏れ**
   - 症状: AGENTS.md でルール更新したが、CLAUDE.md 側が古いままで、矛盾したガイダンスが出る。逆もしかり。
   - パターン例: pdca-workflow.md で「Check NG は最大 3 回まで」と定義したのに、AGENTS.md では「4 回以上は相談」と書かれている。
   - 対応: ここのスキルの Step 3 に「両側確認」を追加。更新対象側の逆側ファイルも必ず確認して同期。

---

## Rule Quality Bar

A good rule is:
- triggered by a concrete situation（上の検出対象パターンのいずれか）
- attached to the step where the miss happens（pdca-workflow の具体フェーズか、coding-standards の禁止ルール）
- objectively checkable（チェックリスト / linting / validation で確認可能）
- short enough to be read during execution（本文は 1 段落以内、チェックリスト項目は 1 文以内）
- explicit about artifacts to update（「pdca-workflow.md の Phase 3 に以下を追加」など）

Avoid:
- vague reminders like "be careful"
- broad personality changes
- rules that require remembering hidden context
- adding new process files when an existing workflow file is the right home
- marking ledger-only updates as committed when the ledger is gitignored

## Before / After: 改善効果の可視化

改善前後の状態を明確にして、ルール最適化の効果を検証します。テンプレート例：

### 例 1: 見落とされた検証ステップ

| 項目 | Before | After |
|---|---|---|
| **症状** | 「Check 未実施のまま PR 作成された」× 3 | Check → PR 作成 の流れが自動確認される |
| **ルール追加** | （記載なし） | pdca-workflow.md Phase 2 Do に「Check 未実施では DO 完了と言わない」明示 |
| **検証方法** | 口頭注意のみ | pdca-workflow.md の「Complete条件」チェックリストで objectively 確認可能 |
| **再発リスク** | 高い | 極低い（DoD に組み込まれたため） |

### 例 2: 重複する条件分岐

| 項目 | Before | After |
|---|---|---|
| **症状** | Codex が「1 ファイルで複数フォーマット規則を適用」 | フォーマット統一ルール、非重複化ガイド |
| **ルール追加** | （記載なし） | coding-standards.md に「1 ファイル 1 フォーマッタ」原則を明記 |
| **検証方法** | コードレビュー時に都度指摘 | linter（ruff format --check）で自動検出 |
| **再発リスク** | 中程度 | 低い（linting gate で catch される） |

### 例 3: 不要な待機処理が混ざる

| 項目 | Before | After |
|---|---|---|
| **症状** | スリープ処理が誤って本番コードに | スリープ禁止ルール、用途別ガイドライン追加 |
| **ルール追加** | （記載なし） | error-recovery.md「必要ないsleep は禁止」+ operations.md「ポーリングは Monitor 活用」 |
| **検証方法** | grep で sleep 検索（手動） | grep ワークアラウンド or pre-commit hook で check |
| **再発リスク** | 高い | 低い（明示的なルール + 検証方法が定義） |

---

## Completion Checklist（実装完了条件）

ルール最適化スキル実行時、以下をすべて確認してから「完了」と宣言する。

| 確認項目 | 確認方法 | 合格基準 |
|---|---|---|
| **Step 1: Root Cause 特定** | missed behavior と trigger timing が書かれているか | 具体的でない（e.g., 「なんか miss があった」）であれば NG |
| **Step 2: ルールホーム判定** | Check Phase パターン + 判定フロー表で home ファイルが決まったか | 複数 home がある場合、優先順が明記されているか確認 |
| **Step 3: 実装タイミング判定** | 単一ファイル vs 複数ファイル更新が判定されたか | 複数ファイル更新の場合、逆側ファイルも同時チェックが計画済みか確認 |
| **Step 3-4: 実装・テスト** | ファイル編集と validation が実行されたか | git diff --check, json tool, quick_validate.py のいずれかで OK を得ているか |
| **Step 4: Ledger 更新** | pending-tasks.md に rule change が記録されたか | gitignored の有無が明記されているか |
| **Final Report 作成** | 以下のセクションがすべて埋まっているか：何が変わったか、なぜ変わったか、どう検証したか、ledger の扱い | テンプレート様式が確認済みか |

---

## Final Report テンプレート

ルール最適化の実施が完了したら、以下のテンプレートで報告を作成します。

```markdown
## Rule Optimization Report

### 発生した Workflow Miss
- [具体的な miss の説明]

### Root Cause
- [判定フロー表で特定された原因]

### 更新対象ファイル
- Primary: [ファイル名]
- Secondary: [関連ファイル、なければ「なし」]

### 変更内容
- [何をどのフェーズに追加したか]

### 検証実行
- `git diff --check`: [OK / NG]
- JSON validation: [該当なし / OK / NG]
- Codex skill validation: [該当なし / OK / NG]

### ルール同期状況
- AGENTS.md / CLAUDE.md: [checked / aligned / not applicable]
- `.claude/skills/*`: [checked / aligned / not applicable]

### Ledger 更新
- pending-tasks.md: [updated / not applicable]
- gitignored: [yes / no]

### 今後の挙動
- [imperative: 「以降、Codex は...する必要がある」「Check NG は...を reject する」など]
```

---

## Report:

ルール最適化スキル実行後、以下を含む最終報告を作成します。

- **which rule files or skills changed**: See the 判定フロー table (Step 2). Updated files are listed in the home column. Primary と Secondary を分けて記載。
- **which `.claude` counterparts were updated or checked**: When updating AGENTS.md, check CLAUDE.md for conflicting guidance. When updating CLAUDE.md, check if Codex skills (.claude/skills/*) need sync updates. Record "checked", "aligned", or "intentionally not changed" in Final Report.
- **which hooks were added or updated**: If user requests automatic enforcement, add hooks under `.claude/hooks/` and register in `.claude/settings.json`. Include hook trigger, script path, and test results.
- **what future behavior is now blocked or required**: Use imperative language. E.g., "After this update, Codex must verify X before Y", "Check NG will now reject Z", "coding-standards enforces no-lambda in all languages".
- **what validation ran**: Report which validation commands executed successfully (git diff --check, json tool, quick_validate.py, linting, etc.).
- **whether `.claude/doc/pending-tasks.md` was updated and whether it is gitignored**: If gitignored, state it clearly. If not, verify the commit includes the ledger update.
