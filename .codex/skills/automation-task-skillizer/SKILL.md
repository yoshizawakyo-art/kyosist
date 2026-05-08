---
name: automation-task-skillizer
description: Turn a user's chat-style description of work they want automated into an autonomous execution workflow and a reusable Skill. Use this whenever the user describes a browser task, local file task, repeated manual operation, or asks to make an automation "skill", even if they provide only a rough natural-language request.
compatibility: Requires local shell access. Browser automation uses Playwright, agent-browser, or an equivalent available browser tool. File automation uses normal workspace file tools. Networked, destructive, credentialed, or paid actions require explicit user confirmation.
---

# Automation Task Skillizer

Convert a chat-style automation request into a repeatable Skill that can safely operate in a browser and on local files.

## Outcomes

Produce one or both of these artifacts, depending on the request:

- **Immediate execution plan**: a concrete checklist the AI can run now against browser pages and local files.
- **Reusable skill**: a `SKILL.md` workflow with optional `scripts/`, `references/`, `assets/`, and `evals/evals.json`.

If the user asks to automate a one-off task, execute it after planning. If they ask to make the automation reusable, create or update a skill.

## Intake From Chat

Extract these fields from the user's message before asking questions:

- **Goal**: what successful completion looks like.
- **Inputs**: URLs, files, folders, credentials needed, form values, target systems.
- **Actions**: browser clicks/forms/downloads, local file reads/writes, API calls, commands.
- **Outputs**: files changed, report generated, data submitted, screenshot captured, confirmation message.
- **Repeatability**: one-off run, daily workflow, reusable skill, or testable automation.
- **Risk**: destructive file changes, external submissions, purchases, messages sent, secrets, personal data.

Ask only for missing information that blocks execution or safety. Prefer a single concise question.

## Safety Gates

Proceed autonomously for low-risk local inspection, local file edits in the requested workspace, and browser navigation that does not submit data.

Pause for explicit confirmation before:

- Deleting, overwriting, or moving broad sets of files.
- Submitting forms, sending messages, purchasing, deploying, publishing, or changing remote state.
- Using credentials, secrets, personal data, payment data, or private third-party accounts.
- Running commands outside the workspace or installing dependencies.
- Accessing sites where automation may violate terms or user intent is unclear.

Never store secrets in the skill. Document required environment variables or manual login steps instead.

## Execution Workflow

1. **Normalize the request**
   - Rewrite the chat request into a numbered task specification.
   - Identify browser operations, local file operations, commands, and success checks.
   - Mark any operation that needs confirmation.

2. **Inspect the environment**
   - Read relevant local files with targeted searches.
   - Check available browser automation tools only when browser work is required.
   - Prefer existing project scripts and conventions over new automation code.

3. **Plan the run**
   - Create a short checklist with inputs, steps, outputs, and verification.
   - Include rollback or recovery notes for file-changing workflows.
   - Split large workflows into stages when more than 2-3 files or tools are involved.

4. **Execute autonomously**
   - For browser work, open the page, wait for stable UI, interact with named controls, and capture evidence such as screenshots, downloaded files, or final page text.
   - For local files, read first, make scoped edits, and verify with deterministic commands.
   - Keep a running log of important observations, files touched, commands run, and blockers.

5. **Verify**
   - Match outputs to the user's success criteria.
   - Run relevant tests, linters, browser checks, or file existence/content checks.
   - Treat a tool's success status as insufficient unless it proves the requested outcome.

6. **Report**
   - Summarize what was done, what changed, how it was verified, and any remaining manual step.
   - Include file paths and command results that matter.

## Reusable Skill Creation

When creating a reusable automation skill, use this structure:

```
<skill-name>/
├── SKILL.md
├── evals/evals.json
├── scripts/        # optional deterministic helpers
├── references/     # optional process notes or schemas
└── assets/         # optional templates or fixtures
```

The `SKILL.md` should include:

- Frontmatter `name` and a pushy `description` that triggers on natural phrases users will actually type.
- A "When to Use" section covering chat-style requests, browser work, local file work, and repeat workflows.
- An intake checklist for required inputs.
- A safety-gate section that says when to pause.
- A deterministic workflow with verification steps.
- Output/reporting format.

Create `evals/evals.json` with 2-4 realistic prompts. Cover at least:

- Browser + local file workflow.
- Local-only file workflow.
- Ambiguous or risky request that should ask for confirmation.

## Skill Draft Template

```markdown
---
name: <skill-name>
description: Use this when the user describes <workflow> in chat and wants the AI to perform it automatically or turn it into a reusable automation. Trigger on phrases like "<natural phrase 1>", "<natural phrase 2>", and "<natural phrase 3>".
---

# <Skill Title>

## When to Use

Use this skill when the user asks to automate <workflow>.

## Intake

- Goal:
- Inputs:
- Browser targets:
- Local files:
- Output:
- Safety confirmations:

## Workflow

1. Normalize the request into a concrete checklist.
2. Inspect required browser pages and local files.
3. Execute low-risk steps autonomously.
4. Pause for high-risk or irreversible actions.
5. Verify each requested output.
6. Report changed files, browser evidence, and remaining manual steps.

## Verification

- Confirm expected files exist or contain the requested content.
- Confirm browser state or downloaded output matches the request.
- Run relevant project checks.
```

## Output Format

When the user asks to create a skill, finish with:

- Skill path.
- What triggers it.
- What browser and file operations it can perform.
- Safety gates.
- Eval prompts added.
- Verification performed.

When the user asks to execute a task now, finish with:

- Completed steps.
- Files changed or browser evidence captured.
- Verification.
- Blockers or confirmations still needed.
