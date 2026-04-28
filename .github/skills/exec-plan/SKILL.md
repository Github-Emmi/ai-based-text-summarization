---
name: exec-plan
description: "Author an ExecutableSpecification (ExecPlan) for phase-based FastAPI backend implementations. Use when starting a new phase, resuming a phase, auditing an existing implementation plan, or writing a self-contained specification that an AI agent can execute without prior context. Produces a numbered, gated, evidence-driven plan document that covers: discovery → gap analysis → phase TODO list → current phase scope → permission gate. Invoke when the user says 'write an ExecPlan', 'plan Phase N', 'spec out the implementation', or 'prepare the next phase'."
argument-hint: "Target phase (e.g. 'Phase 1 — Foundation'), agent file path, and any constraints."
---

# ExecPlan Authoring Skill

An **ExecPlan** (Executable Specification) is a self-contained, evidence-anchored implementation plan that an AI agent can execute step by step with no prior conversation context. It is the authoritative handoff document between planning and implementation.

## When to Use

- Starting any new phase (Phase 0 through Phase 4)
- Resuming a phase after a break (re-verify actual repo state first)
- Handing off implementation to a different agent or session
- Auditing a phase that claims to be complete

## Core Rules (Non-Negotiable)

1. **Read before writing.** Read the agent file, all `docs/`, and every file in the target implementation directory before drafting.
2. **Skeleton first.** Create the phase skeleton (headings, empty sections) and flesh out section by section — never write a wall of text in one pass.
3. **Embed all knowledge.** The executing agent has no internet access and no conversation history. If it needs to know a library API, embed the relevant usage in the plan.
4. **Resolve ambiguity inline.** When two valid approaches exist, pick one, implement it, and explain why in one sentence. Never say "the reader can decide."
5. **Capture evidence.** Every step that produces output must show the expected terminal output, diff excerpt, or test result inside a fenced code block — indented under the step.
6. **Gate every phase.** End with a literal permission gate block. The next phase MUST NOT start until the user types "proceed."

---

## Procedure

### Step 1 — Discovery (always runs first)

```
read: .github/agents/AI-BASED-TEXT-SUMMARIZATION.agent.md
read: docs/00-project-overview.md through docs/11-security-checklist.md
search: backend/ (all .py files)
search: alembic/versions/ (all migration files)
search: tests/ (all test files)
search: docker/ (Dockerfile, docker-compose.yml)
```

Produce a **Repository Summary** block:

```
## 1. Repository Summary

Phase status:
  - Phase 0: [complete / in-progress / not-started]
  - Phase 1: [...]
  - ...

Present files: [list paths verified to exist]
Missing files: [list paths documented but absent]
Contradictions: [docs says X, code does Y — list each]
Last verified: [date of this analysis]
```

### Step 2 — Gap Analysis

Compare every file documented in [docs/04-project-structure.md](../../docs/04-project-structure.md) against what actually exists. For each gap:

```
## 2. Critical Findings

| Severity | File | Issue | Impact | Fix |
|----------|------|-------|--------|-----|
| CRITICAL | backend/app/main.py | Missing — app cannot start | All routes 404 | Create in Phase 1 Step 3 |
| HIGH     | backend/.env.example | Missing — devs have no config reference | Secrets leak risk | Create in Phase 0 Step 4 |
```

Sort by CRITICAL → HIGH → MEDIUM → LOW. Only list items with file evidence.

### Step 3 — Phase Plan Table

Always include the full phase status table even if only one phase is in scope:

```
## 3. Phase Plan

| Phase | Name | Key Deliverable | Status | Acceptance Criteria |
|-------|------|-----------------|--------|---------------------|
| 0 | Repo & Env Bootstrap | GitHub repo, venv, .gitignore | complete | git remote -v shows origin |
| 1 | Foundation | /health → 200, DB pool connected | in-progress | curl /health → {"status":"ok"} |
| 2 | Core Summarization | POST /api/v1/summarize/text → summary | not-started | integration test passes |
| 3 | Advanced Features | Auth + chat + keywords + export | not-started | pytest tests/integration/ passes |
| 4 | Production Hardening | Render deploy live | not-started | curl https://....onrender.com/health |
```

### Step 4 — Current Phase Scope

Write the implementation steps for the **approved phase only**. Use this exact structure per step:

```markdown
### Step N — [Action Verb] [Subject]

**File**: `backend/path/to/file.py`  
**Why**: One sentence explaining why this file is needed at this point.

Create/edit the file with this content:

[implementation block]

Verify:
```bash
[exact command to run]
```
Expected output:
```
[exact expected output or key lines from it]
```
```

### Step 5 — Embed Required Knowledge

Before any step that calls a library for the first time, embed a **Knowledge Block**:

```markdown
> **Knowledge**: asyncpg `Pool.acquire()` returns a connection context manager. Use it as:
> ```python
> async with pool.acquire() as conn:
>     row = await conn.fetchrow("SELECT ...", param)
> ```
> Never call `pool.acquire()` without `async with` — connections will not be returned to the pool.
```

This replaces external documentation links. The executing agent reads this and proceeds correctly.

### Step 6 — Write the Permission Gate

End every ExecPlan with this exact block:

```markdown
---

## Permission Gate

✅ **Phase N scope complete.**

Verified acceptance criteria:
- [ ] [criterion 1 with exact command]
- [ ] [criterion 2 with exact command]

**Next — Phase N+1**: [one-line summary]

Reply with **"proceed"** to start Phase N+1, or describe what to adjust first.
```

---

## Quality Checklist

Before saving the ExecPlan, verify every item:

See [./references/phase-checklist.md](./references/phase-checklist.md) for the full checklist.

---

## Template

See [./references/execplan-template.md](./references/execplan-template.md) for a blank ExecPlan skeleton to start from.

---

## Naming Convention

Save ExecPlans as:

```
docs/execplans/phase-N-<kebab-name>.md
```

Examples:
- `docs/execplans/phase-0-repo-bootstrap.md`
- `docs/execplans/phase-1-foundation.md`
- `docs/execplans/phase-2-core-summarization.md`

---

## Failure Modes to Avoid

| Failure | What Goes Wrong | Correct Approach |
|---------|----------------|------------------|
| "See the architecture docs for the schema" | Executing agent reads no prior context | Paste the exact DDL inline |
| "Use an appropriate library" | Agent picks wrong library | Name the exact package + embed usage |
| "Implement error handling" | Agent adds try/except pass | Specify exact exception classes and response codes |
| "Run the tests" | No test command provided | Write `pytest tests/unit/test_summarizer.py -v` exactly |
| "The usual Docker setup" | Agent generates wrong compose file | Paste the full `docker-compose.yml` content |
| Skipping verification steps | Phase "complete" but app broken | Every step has a verify block with expected output |
| Phase bleeds into next | Too much scope | Strictly enforce the phase boundary — defer anything not in the approved phase |
