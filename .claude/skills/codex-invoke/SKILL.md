---
name: codex-invoke
description: Delegate large-scale implementation to Codex with intelligent multi-stage splitting and parallel execution. Use when splitting complex features across multiple files to avoid token limits, running multiple independent issues simultaneously, or implementing changes requiring staged dependencies (schema → logic → API). Faster and more reliable than manual delegation.
compatibility: Requires mcp__codex-cli__ask-codex tool (Codex CLI MCP server)
---

# Codex Invoke Skill

Delegate implementation work to Codex CLI with a single command.

## When to Use

Use this skill when:

**Scenario 1: Large API implementation spanning multiple files**
- Need to build authentication (schema → service logic → endpoints)
- Complex feature with dependencies between files
- Natural stages: models → business logic → API routes

**Scenario 2: Token limit avoidance**
- Implementation would exceed Codex token limit as a single task
- Break into smaller stages (e.g., DB migration → ORM setup → queries)
- Each stage completes cleanly with its own test/verification

**Scenario 3: Parallel issue execution**
- Multiple independent feature/fix issues ready to implement
- Issues don't block each other (can run concurrently)
- Faster time-to-completion than sequential implementation

**Scenario 4: Complex database work**
- Schema redesign with data backfill
- Multi-table migrations with constraints
- Staged approach reduces risk (migration → verification → application layer)

**Comparison to /pdca**:

| Aspect | `/pdca` | `codex-invoke` |
|---|---|---|
| **Scope** | Full workflow: Plan → Do → Check → Act → PR | Do phase only: intelligent delegation |
| **Use when** | Multiple issues/tasks need full PDCA cycle | Implementation task is clear, just needs to be split/parallelized |
| **Planning** | Claude creates issue definitions | Assumes plan already exists |
| **Execution** | Codex implements + Claude reviews each phase | Codex implements with auto-retry up to 3x |
| **Multi-file complexity** | Handles via /pdca's stage breaking | Direct multi-stage splitting + parallel execution |
| **When NOT to use** | Task is already fully planned and clear | Need full review cycle / PR workflow / architectural validation |

## How to Use

### Simple Usage (Single Implementation)

When delegating a straightforward implementation task:

```
Ask Claude to invoke Codex for your task:
"Please implement <feature description>"

Or explicitly:
"Use codex-invoke to: <task description>"
```

Provide clear details:
- **What** needs to be implemented/fixed
- **Why** (context and requirements)
- **Where** (relevant file paths or directories)
- **Constraints** (tech stack, patterns, dependencies, acceptance criteria)

### Advanced Usage (Multi-Stage or Parallel)

For complex implementations, Claude will automatically invoke codex-invoke with a staged plan:

```
Stage 1 — Models/Schema:
  Implement [schema definition]

Stage 2 — Business Logic:
  Implement [service logic using Stage 1 output]

Stage 3 — API/UI Layer:
  Implement [endpoints/components using Stage 2 output]
```

Or for parallel execution:

```
Parallel Issues:
  Issue A: [feature 1] (independent)
  Issue B: [feature 2] (independent)
  Issue C: [feature 3] (depends on A)
```

## Basic Example

```
Task: Create authentication service in src/api/auth_service.py 
with functions for password hashing (bcrypt), JWT token generation, 
and user validation. Use Pydantic models for input validation.
Include type hints and follow FastAPI conventions.
```

Result:
- ✅ auth_service.py created with all functions
- ✅ Tests pass: `pytest src/api/tests/test_auth.py`
- ✅ Linter passes: `ruff check src/api/`
- Ready for review and integration

## Execution Flow

1. **Claude analyzes task complexity**
   - Single file/simple → direct Codex invocation
   - Multiple files/complex → stage-split plan created

2. **Codex executes**
   - Implements code changes
   - Runs linter/formatter (ruff, Oxlint, etc.)
   - Executes local tests if applicable
   - Auto-retries up to 3 times on failure

3. **Success criteria**
   - Files created/modified per specification
   - Linter/formatter passes without errors
   - Tests pass (if test suite exists)
   - No unexpected side effects or console errors
   - Changes staged locally but NOT committed (Claude reviews first)

## What Codex Returns

- **Code**: Modified/created files ready for review
- **Status**: PASS (all criteria met) or FAIL with details
- **Test results**: If applicable, pass/fail summary
- **Issues**: Any blockers, missing dependencies, or failed retries
- **Next steps**: What needs manual intervention (if any)

## Advanced Patterns

### 1. Multi-Stage Task Splitting（段階的タスク分割戦略）

Use this pattern when complex implementations exceed Codex's token limit or span multiple interdependent files.

**When to split:**
- Implementation spans 3+ files (schema + logic + API layer)
- Multiple dependencies involved (auth, JWT, bcrypt, etc.)
- Clear ordering dependency exists (models → business logic → endpoints)

**Stage-splitting example: Authentication Endpoint**

Invoke Codex in 3 sequential stages:

```
Stage 1: Create Pydantic models for authentication in src/api/schemas/auth.py
→ Implement LoginRequest (email, password) and TokenResponse (access_token, token_type)

Stage 2: Create src/api/auth_service.py using models from Stage 1
→ Implement verify_password (bcrypt), create_access_token (JWT), authenticate_user()

Stage 3: Add POST /api/auth/login to src/api/index.py using auth_service from Stage 2
→ Return 401 on failure, validate with tests
```

**Rules:**
- Each stage references outputs from previous stages
- Keep 1-2 files per stage (aim for <200 lines per invocation)
- Each stage must be independently testable before proceeding to next

**Token limit avoidance examples:**

*Example 1: Large API endpoint (total ~1500 lines if combined)*
```
Stage 1 (350 lines): Pydantic models + DB schema + ORM setup
  File: src/api/schemas/models.py
  
Stage 2 (400 lines): Business logic + service functions
  File: src/api/services/business_logic.py
  
Stage 3 (350 lines): FastAPI endpoints + error handling
  File: src/api/routes/endpoints.py
  
Stage 4 (200 lines): Integration tests
  File: tests/test_endpoints.py
```

*Example 2: Complex migration with verification*
```
Stage 1 (250 lines): DB migration + constraint creation
  File: supabase/migrations/001_schema.sql
  
Stage 2 (300 lines): Data backfill + validation scripts
  File: scripts/backfill_and_verify.py
  
Stage 3 (200 lines): Application layer updates
  File: src/api/index.py (route updates + compatibility layer)
```

Each stage invocation sends ~200-400 tokens (model code) instead of sending entire 1500-line implementation at once.

### 2. Parallel Issue Execution（並列 issue 実装）

Use this pattern when `/pdca` skill produces multiple independent implementation tasks.

**Prerequisites:**
- Claude has completed Plan phase (issues are defined in `.claude/issue/` directory)
- Issues have explicit dependency graph (some may depend on others)
- Each issue has clear acceptance criteria

**並列実行の推奨上限**:
- Maximum 5 concurrent parallel Codex invocations
- Beyond 5 parallel tasks: risk of resource contention, token limit exhaustion, or timeout conflicts
- If more than 5 independent issues exist, batch into groups of ≤5 and execute sequentially per group

**Execution patterns:**

*Sequential with parallel stages:*
```
Issue-A (blocking)
  ↓
Issue-B and Issue-C (parallel, both depend on A)
  ↓
Issue-D, E, F (parallel, all depend on A completion)
```

**Parallel execution example (within 5-concurrent limit):**
```
Batch 1 (Issues A-E parallel):
  Issue-A: DB migration (independent)
  Issue-B: User service (depends on A)
  Issue-C: Auth service (depends on A)
  Issue-D: Notification helper (independent)
  Issue-E: Email template (independent)
  
  Result: 5 issues, 3 dependency tiers
  Codex parallelizes: A + D + E → then B + C (after A)

Batch 2 (Issues F-J parallel):
  [Repeat after Batch 1 completes]
```

**Instructions format:**
```
Invoke Codex for parallel implementation:
1. issue-auth-migration (first — blocking)
2. issue-user-profile (after #1) 
3. issue-settings-page (after #1)

Each issue references: .claude/issue/<name>/issue.md
Verify after each: local tests PASS, console errors cleared, ruff/linter PASS
```

**Workflow:**
1. Analyze dependencies from issue definitions
2. Implement Phase 1 sequentially (Issue-A)
3. Implement Phase 2 in parallel (Issue-B, Issue-C)
4. Verify all issues independently pass tests
5. Report completion status per issue

### 3. Error Recovery Protocol（エラー時の自動対応・最大 3 回リトライポリシー）

**自動リトライポリシー**: Codex automatically retries up to **3 times maximum** when task failures occur.

| Retry Attempt | Strategy | When to expect |
|---|---|---|
| Attempt 1 | Initial execution | First run of the task |
| Attempt 2 (retry 1/3) | Alternate implementation approach | If Attempt 1 failed; Codex tries different pattern or debugging path |
| Attempt 3 (retry 2/3) | Deep refactoring + root cause analysis | If Attempt 2 failed; Codex refactors core logic |
| Report to Claude (no retry 3/3) | Manual investigation required | All 3 attempts exhausted |

**Error handling per type:**

| Error Type | Codex Auto-Action | Example |
|---|---|---|
| Code generation error | Retry with different approach (attempt 2-3) | Schema validation logic fails type checking |
| Test failure | Fix test or implementation logic (attempt 2-3) | Import errors, type mismatches, assertion failures |
| Linter error | Correct style/format violations (attempt 2) | Unused imports, line length violations, naming conventions |
| Auth/permission error | Debug env config or permissions (attempt 2) | Missing JWT_SECRET, API key, file permissions |
| Timeout/resource error | Reduce scope and re-attempt (attempt 2-3) | Task too large, parallel execution conflict |
| Dependency not found | Install missing package or update imports (attempt 2) | Missing library, incorrect module path |

**Detailed auto-retry flow:**
```
Attempt 1: Initial implementation
  ✅ Success → Task complete, proceed to next stage
  ❌ Error → Move to Attempt 2

Attempt 2/3 (Max 2 retries):
  - Analyze failure logs
  - Try alternate implementation approach
  - Refactor core logic if needed
  - Re-run tests and linter
  ✅ Success → Task complete, proceed to next stage
  ❌ Error → Try Attempt 3

Attempt 3 (Final retry):
  - Deep root cause analysis
  - Refactor fundamental approach if necessary
  - Re-run comprehensive tests
  ✅ Success → Task complete, proceed to next stage
  ❌ All attempts exhausted → Report to Claude with full logs
```

**When all 3 attempts fail, Codex will:**
- Stop any parallel execution in progress
- Report failure reason with detailed error logs and diagnostic information
- List what was attempted in each of the 3 attempts
- Wait for Claude to investigate and provide new direction (scope change, architecture decision, manual fix)

## Edge Cases & Troubleshooting

**Q: What if Stage 2 depends on Stage 1, but Stage 1 fails?**
- Do not proceed to Stage 2. Report Stage 1 failure details. Claude will investigate before retrying Stage 1.

**Q: Can I run all stages simultaneously if they have dependencies?**
- No. Stages with ordering dependencies (e.g., schema → logic → API) must execute sequentially. Stages with NO dependencies can run in parallel.

**Q: What if parallel execution shows conflicts between Issue-B and Issue-C?**
- Codex detects conflicts and reports them. Claude re-evaluates dependency graph and may reorder execution (sequential instead of parallel).

**Q: How long can a single stage implementation take?**
- Codex has a default execution timeout (typically 5-10 minutes depending on complexity). Very large implementations may need further splitting.

**Q: What if a stage creates 100+ lines but the requirement was "minimal changes"?**
- Codex will note this and flag for review. Check if the stage can be split further or if the scope was misunderstood. Claude makes final judgment.

## Tips

- Be specific about file paths, functions, and acceptance criteria
- Include relevant code patterns or existing implementations to follow
- Mention testing expectations explicitly ("should pass X test")
- Reference architecture docs or style guides if the project has them
- For parallel execution, clearly state dependencies ("Issue B blocks on Issue A")
- For error cases, include exact error logs or symptoms you're seeing
