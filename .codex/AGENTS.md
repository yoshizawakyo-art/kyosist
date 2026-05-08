# AGENTS.md

## 🧭 Purpose

This repository uses a hybrid workflow originally designed for Claude Code.
Codex must follow these rules and reuse the existing `.agent/claude` definitions.

---

## 📁 Directory Structure Awareness

* `.agent/claude/agents/` → agent definitions (role-based instructions)
* `.agent/claude/skills/` → reusable workflows and domain knowledge
* `.agent/claude/commands/` → task-specific execution patterns

Codex MUST treat these as authoritative references.

---

## 📖 Mandatory Reading Rule

Before performing any task:

1. Identify if the task matches an existing agent or skill
2. If matched, READ the corresponding file:

   * Agents → `.agent/claude/agents/*.md`
   * Skills → `.agent/claude/skills/**/SKILL.md`
3. Follow the instructions in those files unless they conflict with this document

DO NOT ignore these files.

---

## 🧠 Agent Mapping

Use the following mappings when applicable:

* **PDCA Check / Review tasks**
  → `.agent/claude/agents/pdca-check-reviewer.md`

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
→ Search `.agent/claude/skills/` and load relevant SKILL.md

---

## 🧩 Behavior Expectation

Codex should behave as:

* a careful maintainer (not a fast coder)
* a reviewer as well as an implementer
* a system-aware agent that respects existing design

---

## 📝 Notes

* `.agent/claude` is the source of truth for workflow intelligence
* This file acts as the bridge between Claude-style and Codex-style execution

---
