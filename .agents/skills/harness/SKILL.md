---
name: harness
description: "Audits and optimizes the AI agent harness for the current project: CLAUDE.md, AGENTS.md, rules, skills, tool permissions, hooks, task state, validation loops, evaluator separation, and entropy cleanup. Use when the user says '/harness', 'harness engineering', 'optimize the harness', 'improve how Claude/Codex works here', 'set up the agent environment', or asks to review CLAUDE.md, AGENTS.md, .claude/rules, .claude/skills, hooks, settings, or task ledgers."
---

# Harness Optimization

Use this skill to improve the environment around an AI agent. Treat the agent as:

```text
Agent = Model + Harness
```

The harness is the project-visible system of context, constraints, tools, state, feedback, and cleanup that makes agent work reliable. Optimize the operating environment, not just prompts.

## Core Principles

- **Context engineering**: Keep the repository as the single source of truth. Put durable decisions, commands, task state, architecture notes, and local conventions on disk where agents can read them.
- **Architectural constraints**: Prefer linters, formatters, tests, schema checks, CI, hooks, and file structure over broad instructions like "write good code".
- **Entropy management**: Detect and remove stale docs, duplicated rules, dead generated files, and AI-created slop before they shape future agent behavior.
- **Generator/evaluator separation**: Separate creation from review when quality matters. Use an independent reviewer, test suite, rubric, or judge prompt instead of relying only on the generator's self-assessment.
- **State persistence**: Do not trust the context window as memory. Persist task state in structured files when possible; use JSON for machine-owned state and Markdown for human-facing ledgers.
- **Critical vigilance**: A polished harness can make wrong output look trustworthy. Keep explicit verification gates and surface assumptions.

## Workflow

### 1. Read the Harness Surface

Inspect only the files that exist; do not invent a harness layout.

- Agent instructions: `AGENTS.md`, `CLAUDE.md`, `.agents/AGENTS.md`
- Rule layers: `.claude/rules/*.md`, `.agents/rules/*.md`
- Skills: `.claude/skills/*/SKILL.md`, `.agents/skills/*/SKILL.md`, `~/.codex/skills/*/SKILL.md`, project `skills/*/SKILL.md`
- Commands: `.claude/commands/*.md`, `.agents/commands/*.md`
- Settings and hooks: `.claude/settings*.json`, `.agents/settings*.json`, `.claude/hooks/*`, `.agents/hooks/*`, project automation files
- State: `.claude/doc/pending-tasks.md`, `.agents/doc/pending-tasks.md`, handoff files, task JSON, issue/PR notes
- Validation: `package.json`, `pyproject.toml`, `requirements.txt`, `vercel.json`, CI config, test directories
- Recent drift: `git status --short`, `git log --oneline -10`

For this repository, obey the task ledger rule: read `.claude/doc/pending-tasks.md` before continuation work and update it after any work that changes files, verification status, task status, blockers, or next steps.

### 2. Score the Harness

Score each dimension from 0 to 5 and cite concrete files.

| Dimension | What to Check |
|---|---|
| Context | Commands, stack, architecture, decisions, and local conventions are accurate, concise, and discoverable. |
| Constraints | Style, architecture, security, and workflow expectations are enforced mechanically where practical. |
| Tools | Permissions, connectors, scripts, and commands allow routine read/build/test work without unsafe broad access. |
| Feedback | Tests, lint, type checks, browser checks, CI, and review rubrics are documented and runnable. |
| State | Tasks, decisions, blockers, and handoffs are persisted with clear ownership and update gates. |
| Evaluators | Generation and evaluation are separated for risky work through reviewers, subagents, CI, or judge prompts. |
| Entropy | Stale docs, duplicated rules, orphaned files, and generated clutter have cleanup paths. |

### 3. Produce an Optimization Plan

Report in this shape:

```markdown
## Harness Audit: <repo/workflow>

### Scores
- Context: <0-5> — <file-grounded reason>
- Constraints: <0-5> — <file-grounded reason>
- Tools: <0-5> — <file-grounded reason>
- Feedback: <0-5> — <file-grounded reason>
- State: <0-5> — <file-grounded reason>
- Evaluators: <0-5> — <file-grounded reason>
- Entropy: <0-5> — <file-grounded reason>

### High Impact
1. <specific change and file path>

### Medium Impact
- <specific change and file path>

### Leave Alone
- <working part that should not be churned>
```

If the user asked for an audit only, stop after the report. If the user asked to optimize or create/update harness files, implement the smallest high-impact changes after the audit.

### 4. Implement Narrow Changes

Choose durable homes carefully:

- `AGENTS.md`: Codex-facing repository requirements.
- `CLAUDE.md`: Claude-facing project requirements.
- `.claude/rules/*.md` and `.agents/rules/*.md`: workflow, safety, coding, architecture, and domain rules.
- `.claude/skills/<name>/SKILL.md`, `.agents/skills/<name>/SKILL.md`, and `~/.codex/skills/<name>/SKILL.md`: reusable workflows.
- `.claude/commands/<name>.md` and `.agents/commands/<name>.md`: slash-command entry points that explicitly invoke skills.
- `.claude/hooks/*` and `.agents/hooks/*`: deterministic reminders or gates that should not rely on model memory.
- `.claude/doc/pending-tasks.md`: task status, completed work, blockers, verification.

When adding or changing a skill/rule/command, keep Codex and Claude counterparts behaviorally aligned. Mirror triggers, gates, validation, and ledger requirements; exact wording may differ.

### 5. Validate

Run the cheapest relevant checks:

- Skills: `python3 /home/yoshizawa/.codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>`
- JSON settings/state: `python3 -m json.tool <file>`
- Rule/docs edits: `git diff --check -- <changed-files>`
- Python projects: `ruff check .` and `ruff format --check .` when Python behavior or rules changed
- Frontend harness or UI checks: run the documented local tests when affected

If validation is skipped, state the reason and record any remaining blocker in the task ledger when the repo uses one.

## Harness Patterns

Use these patterns when they solve an observed failure:

- **Session protocol**: one session per task, baseline verification at session start, task ledger update at completion.
- **Structured state**: JSON for machine-mutated progress; Markdown ledgers for human-readable project history.
- **Completion gates**: require test/verification status before final reports.
- **Safety gates**: block destructive shell/git operations or secret exposure through hooks or explicit policy.
- **Quality loops**: run deterministic format/lint/test checks after edits.
- **Cleanup loop**: periodically remove stale generated artifacts and reconcile docs with code.

Avoid rules that are vague, duplicated across too many files, impossible to verify, or so strict that they prevent reasonable agent judgment.
