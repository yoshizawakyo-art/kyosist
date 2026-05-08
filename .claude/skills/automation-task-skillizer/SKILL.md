---
name: automation-task-skillizer
description: |
  Use this when a user describes a repetitive manual task in plain language—like "fill out a form across 50 pages", "export data from a site daily", "batch-rename files by pattern", "scrape a table and save to CSV"—and wants the AI to either run it now or turn it into a reusable automation skill. Detects intent even from rough, incomplete descriptions. Triggers on phrases: "automate this", "make a skill for", "run this repeatedly", "I have to do this every day", "can you extract", "generate a report by scraping", "batch process these files", "fill out forms on a site", "download and organize".
compatibility: Requires local shell access and file system access. Browser automation uses Playwright (preferred), agent-browser, or a similar available browser tool. File automation uses standard workspace file tools (Read, Write, Bash). Networked, destructive, credentialed, or paid actions require explicit user confirmation. No external API keys stored in the skill itself.
---

# Automation Task Skillizer

Convert a user's chat-style automation request into an immediately executable workflow or a reusable, documented automation skill that runs in a browser and on local files.

## When to Use

**Trigger scenarios**:
1. **One-off browser automation**: "Download all my receipts from this site", "Fill in this form 20 times with different data", "Screenshot every product page"
2. **Batch file processing**: "Rename 500 files by pattern", "Extract emails from all CSVs in a folder", "Convert JPEG to PNG for my project"
3. **Data extraction/reporting**: "Scrape this table daily and email it", "Generate a report by combining CSVs and uploading to Drive"
4. **Recurring manual task**: "I repeat this every Monday", "This form takes 10 minutes to fill — can we automate it?"
5. **Skill creation**: "Turn this into a reusable skill so others can use it"

**Do not use if**:
- The user is asking for general programming help (not automation of a specific task)
- The task is purely conceptual (not actionable in a browser or file system)

## Outcomes

Produce one or both of these artifacts, depending on the request:

- **Immediate execution plan**: a concrete, ordered checklist the AI can execute now against browser pages and local files, including verification steps.
- **Reusable skill**: a `SKILL.md` workflow with optional `scripts/`, `references/`, `assets/`, and `evals/evals.json`, ready to be invoked again or by others.

**Decision logic**:
- If the user says "do this now" → create an execution plan and run it.
- If the user says "make this repeatable" or "create a skill" → create a `SKILL.md` and document triggers, inputs, and outputs.
- If the user describes a task without specifying → ask in a single concise question whether they want it run once or reused.

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

### Step 1: Normalize and Intake

1. Extract from the user's message:
   - **Goal**: What successful completion looks like (verb + desired output).
   - **Inputs**: URLs, files, folders, credentials, form data, config needed.
   - **Actions**: Browser clicks, form fills, downloads, file reads/writes, commands, API calls.
   - **Outputs**: Files changed, report generated, form submitted, screenshot captured.
   - **Repeatability**: One-off run, daily/weekly, reusable skill, or testable automation.
   - **Risk level**: Destructive file changes, external submissions, credential use, payment, messages sent.

2. Ask only for **missing information that blocks execution or safety**.
   - Example (good): "I see you want to rename 500 files. Do you have the naming rules in a CSV, or should I ask for them separately?"
   - Example (bad): "Can you describe the site's authentication flow?" (save for Step 2 if browser work is needed)

### Step 2: Inspect the Environment

1. For **browser work**: Read the target page HTML or navigate to preview the form/interface.
2. For **file work**: Read a sample file to understand structure (CSV headers, JSON schema, etc.).
3. For **commands**: Verify any required tools are available (e.g., `jq`, `ffmpeg`).
4. **Prefer existing project conventions** over new automation code (e.g., use existing scripts, form selectors if documented).

### Step 3: Plan the Run

Create a short checklist:
```
Inputs: [list files/URLs]
Steps:
  1. [step]
  2. [step]
  ...
Outputs: [file paths or state changes]
Verification: [check command or visual confirmation]
Rollback: [how to undo if needed]
```

Split workflows into **stages** if they touch >2-3 files or require >3 separate tools.

### Step 4: Execute Autonomously

**For browser work**:
- Open the page, wait for stable UI (no loading spinners).
- Interact with named controls (buttons, form fields, links).
- Capture evidence: screenshots, downloaded files, final page text.
- Keep a log of clicks, data entered, responses received.

**For local files**:
- Read first to understand structure.
- Make scoped edits (change only what's requested, not the entire file).
- Use deterministic commands (e.g., `sed`, `jq`, Python scripts).
- Verify each edit as you go.

**Example: Batch file processing**
```
FOR each file in input_folder:
  1. Read file.
  2. Transform (rename, convert, extract).
  3. Write to output_folder.
  4. Verify output exists and has correct size.
END
```

### Step 5: Verify and Error Recovery

1. **Match outputs to user's success criteria**:
   - Count of files processed = expected count?
   - Output file content correct?
   - Browser form submitted successfully?

2. **Run checks**:
   - File existence and content verification.
   - Browser page state (e.g., "Success" message visible).
   - Command exit codes.

3. **If something fails**:
   - Log the error message exactly.
   - Identify the step where it failed.
   - Propose a fix (retry, skip, ask for clarification).
   - Do not silently skip failures.

### Step 6: Report

Summarize:
- **What was done**: Task description and approach.
- **What changed**: Files modified, browser actions, data submitted.
- **Verification**: How success was confirmed (e.g., "Processed 450/450 files, 0 errors").
- **Any remaining manual step**: If skill was created, user can trigger it with `/skill-name`; if task ran once, note any follow-up needed.

**Example output**:
```
## Execution Summary

Task: Batch rename 500 product images by SKU

Inputs:
- Source folder: /uploads/products/
- SKU mapping: SKU_mapping.csv (500 rows)

Actions:
1. Read mapping file (500 SKUs)
2. For each SKU, found matching image file
3. Renamed using pattern: {sku}_product.jpg
4. Moved to /organized/products/

Outputs:
- 500 files renamed and moved
- Log: processed_files.csv (attached)

Verification:
- File count in source: 500 → destination: 500 ✓
- Spot-checked 10 renames: all correct ✓
- No files left in source: ✓

Skill created:
- Name: batch-image-renamer-by-sku
- Trigger: "rename product images by SKU"
```

## Reusable Skill Creation

When creating a reusable automation skill, use this structure:

```
<skill-name>/
├── SKILL.md
├── evals/evals.json
├── scripts/        # optional deterministic helpers (Python, bash, JS)
├── references/     # optional process notes, API schemas, form field lists
└── assets/         # optional templates, fixtures, sample data
```

### SKILL.md Template

The `SKILL.md` should include:

- **Frontmatter** (`name`, `description`): Explicit trigger phrases users will actually type, with concrete scenarios.
- **When to Use**: Chat-style examples for each use case.
- **Intake**: Checklist of required inputs (URLs, file paths, credentials, form data).
- **Safety Gates**: When to pause for confirmation (destructive, external state change, credential use).
- **Execution Workflow**: Step-by-step, numbered, deterministic.
- **Verification**: Explicit checks to confirm success.
- **Edge Cases / Error Recovery**: How to handle if something goes wrong.
- **Output Format**: What the user receives when done.

### Example: Email Bulk Sender Skill

```markdown
---
name: email-bulk-sender-via-web
description: Use this when a user wants to send the same email to a list of addresses through a web interface (Gmail, Outlook, a custom form), and either run it now or create a reusable skill. Triggers on: "send emails in bulk", "automate sending to 50 people", "fill out this form for each recipient", "email blasts".
---

# Email Bulk Sender (Web)

## When to Use
- User has a list of email addresses or recipient data in a file or folder.
- User has a web interface (Gmail, custom site) to send emails.
- User wants to avoid manual repetition (50+ emails, daily sends).

## Intake
- Email list (CSV, Excel, plain text, one per line)
- Email subject and body (template with placeholders like {name}, {email})
- Target URL or service
- Safety confirmation if external emails are involved

## Workflow
1. Read email list and template.
2. Open web interface and authenticate (if needed).
3. For each recipient:
   - Fill form/compose field with substituted template.
   - Submit or send.
   - Wait for confirmation.
4. Verify sent count matches list count.
5. Capture screenshot and log of sent addresses.

## Verification
- Confirm number of sent emails = number in list.
- Spot-check a few sent emails in recipient's inbox (if accessible).

## Edge Cases
- **Rate limiting**: If service rejects sends, add delays between submissions.
- **Failures**: Log and resume from last successful send.

## Output
- CSV log of sent addresses with timestamps.
- Success/failure count.
```

### Create `evals/evals.json`

Include 2-4 realistic test prompts to verify the skill works:

```json
{
  "evals": [
    {
      "prompt": "I have 50 product images in a folder and need to resize them all to 800x600 and save as PNG. Can you do this now?",
      "expected": "Autonomously process images, verify output, report success or blockers"
    },
    {
      "prompt": "Create a skill that lets me scrape a product price from a website every day at 9 AM and log it.",
      "expected": "Create SKILL.md with schedule trigger, browser steps, and storage logic"
    },
    {
      "prompt": "I need to fill out a form on an internal site 100 times with different data from my CSV.",
      "expected": "Ask for CSV sample or confirm before submitting external data"
    }
  ]
}
```

## Edge Cases and Error Recovery

### Scenario: Form Submission Fails

**Symptom**: Browser automation fills form but submit button doesn't work or page doesn't navigate.

**Recovery**:
1. Log the exact error message (screenshot or console output).
2. Check for JavaScript errors or validation messages.
3. Retry with a slight delay before submit (Playwright: `await page.waitForTimeout(500)`).
4. If still fails, check if credentials were incorrect or the form is locked.
5. Fall back to manual submission and report the blocker.

### Scenario: File Batch Processing Crashes Mid-Way

**Symptom**: Processing 500 files but crashes at file 347.

**Recovery**:
1. Log which file caused the crash.
2. Resume from file 348 on the next run (store progress in a checkpoint file).
3. Report which file failed and why (corrupt format, unsupported encoding, etc.).

### Scenario: Browser Timeout or Network Issues

**Symptom**: Page takes >10 seconds to load or connection drops.

**Recovery**:
1. Increase timeout: `await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 })`
2. Retry once with exponential backoff.
3. If persistent, check if the site is down or blocking the automation.

### Scenario: Secrets or Credentials Asked For

**Symptom**: User says "automate login to my bank account" or "use my API key".

**Recovery**:
1. Never ask for or store credentials in the skill.
2. Document that manual login is required: "Please log in once; the script will use the authenticated session."
3. For API keys, direct the user to set them in `.env`: `GITHUB_TOKEN=<your_token>`

## Output Format

### When Creating a Reusable Skill

Finish with:

```
## Skill Created

**Path**: `~/.claude/skills/my-automation-skill/SKILL.md`
**Triggers on**: "automate [X]", "batch process [Y]", "extract [Z]"
**Browser operations**: Form fill, navigation, screenshot, file download
**File operations**: Read CSV, batch rename, aggregate data
**Safety gates**: Pauses before submitting external forms, deleting files
**Eval prompts**: 2 test cases added to `evals/evals.json`
**Verification**: Test ran successfully with sample data
```

### When Executing a One-Off Task

Finish with:

```
## Task Execution Summary

**Goal**: [what was automated]
**Inputs**: [URLs, files used]
**Outputs**: [files created, data extracted, forms submitted]
**Verification**: [how success was confirmed]
**Blockers**: [any manual steps still needed]

Files changed: [list with paths]
Evidence: [screenshot filenames or downloaded files]
```
