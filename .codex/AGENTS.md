# AGENTS.md

## 🧭 Purpose

This repository uses a hybrid workflow originally designed for Claude Code.
Codex must follow these rules and reuse the existing `.claude/` and `.agents/` definitions.

---

## 📁 Directory Structure Awareness

* `.claude/agents/` and `.agents/agents/` → agent definitions (role-based instructions)
* `.claude/skills/` and `.agents/skills/` → reusable workflows and domain knowledge
* `.claude/commands/` and `.agents/commands/` → slash-command entry points

Codex MUST treat these as authoritative references.

---

## 📖 Mandatory Reading Rule

Before performing any task:

1. Identify if the task matches an existing agent or skill
2. If matched, READ the corresponding file:

   * Agents → `.claude/agents/*.md` and `.agents/agents/*.md`
   * Skills → `.claude/skills/**/SKILL.md` and `.agents/skills/**/SKILL.md`
   * Commands → `.claude/commands/*.md` and `.agents/commands/*.md`
3. Follow the instructions in those files unless they conflict with this document

DO NOT ignore these files.

---

## 🧠 Agent Mapping

Use the following mappings when applicable:

* **PDCA Check / Review tasks**
  → `.claude/agents/pdca-check-reviewer.md` and `.agents/agents/pdca-check-reviewer.md`

(Extend this mapping as new agents are added)

---

## 🔄 Workflow: PDCA

All tasks must follow this workflow:

### 1. Plan

* Understand the task
* Identify affected files
* Check for existing patterns

### 2. Do

* Implement minimal necessary changes
* Avoid touching unrelated code

### 3. Check

* Review your own changes
* Use `pdca-check-reviewer` if applicable
* Validate:

  * Logic correctness
  * Edge cases
  * Consistency with existing code

### 4. Act

* Suggest improvements only after verification
* Do not introduce speculative changes

---

## ⚙️ Execution Rules

### Code Changes

* Do NOT modify unrelated files
* Follow existing architecture and conventions
* Prefer minimal diff

### Validation

* Run or recommend:

  * tests
  * lint
  * type checks

### Output Requirements

Always include:

* What was changed
* Why it was changed
* How it was verified

---

## 🚫 Safety Constraints

* Do NOT execute destructive operations unless explicitly required
* Do NOT bypass safeguards unnecessarily
* Avoid broad file rewrites

---

## 📚 Skill Loading Heuristic

If a task resembles:

* a known workflow
* repeated implementation pattern
* domain-specific logic

Then:
→ Search `.claude/skills/` and `.agents/skills/`, then load the relevant `SKILL.md`

---

## 🧩 Behavior Expectation

Codex should behave as:

* a careful maintainer (not a fast coder)
* a reviewer as well as an implementer
* a system-aware agent that respects existing design

---

## 🔴 Credit Management Rule (Critical)

When Claude's API credit falls below 5%:

1. **Handoff Document Creation**
   - File: `.claude/doc/session-handoffs/session-handoff-<YYYY-MM-DD>.md`
   - Must include: current implementation status, CHECK/CHECK NG results, required fixes, next session commands
   - Execute immediately when 5% threshold is detected

2. **Report to User**
   - Summarize handoff document content
   - Provide exact command for next session
   - Do NOT attempt repairs with remaining credit

3. **Prohibited Actions**
   - Do NOT start Codex execution near 5% threshold
   - Do NOT leave fixes partially applied
   - Do NOT commit incomplete work

(Detail: See `.claude/rules/` → operations.md / error-recovery.md)

---

## 🔗 Synchronization Rule (Critical)

When adding rules, skills, hooks, or slash commands:

1. **Always update both sides**:
   - Claude side: `CLAUDE.md`, `.claude/rules/`, `.claude/skills/`
   - Codex side: `.agents/AGENTS.md`, `.agents/rules/`, `.agents/skills/`, `.agents/commands/`

2. **Same turn requirement**:
   - New rule → update CLAUDE.md + `.agents/AGENTS.md` in same commit
   - New skill → create in `.claude/skills/` + `.agents/skills/` simultaneously
   - New slash command → create in `.claude/commands/` + `.agents/commands/` simultaneously
   - New hook → register in both `.claude/settings.local.json` and `.agents/settings.local.json`

3. **Verify after update**:
   - Check file existence and correctness on both sides
   - Update `.claude/doc/pending-tasks.md` with sync status
   - After any work changes files, verification status, task status, blockers, or next steps, update `.claude/doc/pending-tasks.md` before the final response, including rule/documentation-only changes

(Detail: See CLAUDE.md → "ルール / Skill 整合性必須")

---

## 📝 Notes

* `.claude/` and `.agents/` together are the source of truth for workflow intelligence
* This file acts as the bridge between Claude-style and Codex-style execution
* Both Claude (`CLAUDE.md`) and Codex (`.agents/AGENTS.md`) must be kept in sync

---
