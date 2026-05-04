---
description: Create, improve, and evaluate Codex skills using the local skill-creator workflow.
---

# Skill Creator

Use this command when the user wants to create a new Codex skill, improve an existing skill, run skill evals, or tune a skill description.

## Preflight

1. Read `.agents/skills/skill-creator/SKILL.md`.
2. Confirm the target skill path if the user already named one.
3. If the user has not provided a target, infer whether this is:
   - new skill creation
   - existing skill improvement
   - eval/benchmark work
   - description tuning
4. Check whether the required helper directories exist:
   - `.agents/skills/skill-creator/scripts/`
   - `.agents/skills/skill-creator/references/`
   - `.agents/skills/skill-creator/eval-viewer/`

## Plan

Follow the workflow in `.agents/skills/skill-creator/SKILL.md`.

For new skills:
1. Capture intent and success criteria.
2. Draft `SKILL.md`.
3. Create 2-3 realistic eval prompts when useful.
4. Validate the skill.

For existing skills:
1. Read the current skill.
2. Identify the user's requested change.
3. Patch only the relevant files.
4. Validate the result.

## Commands

Use these commands when relevant:

```bash
python3 .agents/skills/skill-creator/scripts/quick_validate.py <skill-directory>
```

```bash
python3 -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
```

```bash
python3 .agents/skills/skill-creator/eval-viewer/generate_review.py <workspace>/iteration-N --skill-name <name>
```

Run helper scripts from the correct working directory when they rely on relative imports.

## Verification

After edits:
1. Run `quick_validate.py` for every modified skill.
2. Confirm the frontmatter has `name` and `description`.
3. Confirm the description says when the skill should trigger.
4. Confirm bundled references/scripts are only loaded when needed.

## Summary

Report:
- files changed
- validation result
- how the user should invoke the skill

## Next Steps

Suggest the next practical action only when it directly follows from the work, such as adding evals, running a benchmark, or tuning the description.
