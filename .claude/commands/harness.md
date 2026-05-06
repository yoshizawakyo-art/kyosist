---
description: Audit and optimize this repository's AI agent harness.
allowed-tools: Read, Glob, Grep, LS, Bash, Edit, MultiEdit, Write
---

Use the `harness` skill for this request.

Audit and optimize the current repository harness with special attention to:

- `CLAUDE.md`, `AGENTS.md`, and `.agents/AGENTS.md`
- `.claude/rules/` and `.agents/rules/`
- `.claude/skills/`, `.agents/skills/`, and `~/.codex/skills/`
- `.claude/commands/` and `.agents/commands/`
- `.claude/settings*.json`, `.agents/settings*.json`, and hooks
- `.claude/doc/pending-tasks.md`

Follow the skill workflow, implement the smallest high-impact changes when optimization is requested, validate changed files, and update `.claude/doc/pending-tasks.md` before the final response.
