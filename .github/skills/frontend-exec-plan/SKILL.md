---
name: frontend-exec-plan
description: "Author an ExecutableSpecification (ExecPlan) for phase-based Next.js frontend implementations for the AI-Based Text Summarization Platform. Use when starting a new frontend phase, resuming a phase, auditing an existing frontend plan, or writing a self-contained specification that an AI agent can execute without prior context. Produces a numbered, gated, evidence-driven plan document covering: discovery → gap analysis → phase TODO list → current phase scope → permission gate. Invoke when the user says 'write frontend ExecPlan', 'plan FE Phase N', 'spec out frontend', or 'prepare next frontend phase'."
argument-hint: "Target phase (e.g. 'FE-1 Auth'), agent file path, and any constraints."
---

# Frontend ExecPlan Authoring Skill

A **Frontend ExecPlan** is a self-contained, evidence-anchored implementation plan that an AI agent can execute step by step with no prior conversation context, specifically for the Next.js frontend of the AI-Based Text Summarization Platform.

## When to Use

- Starting any new frontend phase (FE-0 through FE-6)
- Resuming a phase after a break
- Handing off to a different agent or session
- Auditing a frontend phase that claims to be complete

## Core Rules

1. **Read before writing.** Read agent file, all `docs/`, and every file in `frontend/src/` before drafting.
2. **Backend contract first.** Every UI feature must map to a specific backend endpoint — embed the request/response shape.
3. **Component → Page → Route.** Build leaf components first, then compose into pages, then wire routes.
4. **Types before implementation.** Define TypeScript interfaces matching backend response shapes before writing components.
5. **Embed all knowledge.** The executing agent has no internet access. Embed relevant library APIs inline.
6. **Gate every phase.** End with a literal permission gate. Next phase MUST NOT start until user types "proceed."

---

## Procedure

### Step 1 — Discovery

```
read: .github/agents/FRONTEND-AI-SUMMARIZATION.agent.md
read: docs/06-api-design.md       (all endpoints + shapes)
read: docs/00-project-overview.md (requirements)
search: frontend/src/             (existing components, pages, lib)
search: frontend/package.json     (installed deps)
```

Produce a **Repository Summary** block:

```markdown
## 1. Frontend Repository Summary

Phase status:
  - FE-0 Scaffold: [complete / in-progress / not-started]
  - FE-1 Auth:     [...]
  ...

Present files: [list verified paths]
Missing files: [list expected-but-absent paths]
Backend endpoints covered by UI: [list]
Backend endpoints NOT YET covered: [list]
Last verified: [date]
```

### Step 2 — Gap Analysis

```markdown
## 2. Critical Findings

| Severity | File/Feature | Issue | Impact | Fix |
|----------|-------------|-------|--------|-----|
| CRITICAL | frontend/src/lib/api/client.ts | Missing — no HTTP client | All API calls broken | Create in FE-0 Step 2 |
| HIGH | Auth token refresh | 401 not handled | Users logged out unexpectedly | Add axios interceptor FE-1 |
```

### Step 3 — Phase Plan Table

```markdown
## 3. Phase Plan

| Phase | Name | Key Deliverable | Status | Acceptance Criteria |
|-------|------|-----------------|--------|---------------------|
| FE-0 | Scaffold | Next.js + Tailwind + shadcn + Zustand + axios | not-started | npm run dev → 3000 |
| FE-1 | Auth | Login + Register + token flow | not-started | Login → dashboard redirect |
| FE-2 | Summarize | Text + PDF upload + result | not-started | POST /summarize/text → summary shown |
| FE-3 | History | List + filter + delete | not-started | History paginates correctly |
| FE-4 | Chat | Session + messages | not-started | Chat sends and receives |
| FE-5 | Export + Profile | PDF download + profile update | not-started | PDF downloads |
| FE-6 | Polish + Deploy | Skeletons + errors + deploy | not-started | Live URL 200 |
```

### Step 4 — Current Phase Scope

Per step, use this exact structure:

```markdown
### Step N — [Action Verb] [Subject]

**File**: `frontend/src/path/to/file.tsx`
**Why**: One sentence explaining why this is needed now.

[implementation block]

Verify:
```bash
[exact command]
```
Expected:
```
[exact output]
```
```

### Step 5 — Embed Required Knowledge

Before calling a library for the first time, embed a **Knowledge Block**:

```markdown
> **Knowledge**: shadcn/ui Button usage:
> ```tsx
> import { Button } from "@/components/ui/button"
> <Button variant="default" size="sm" onClick={handleClick}>Submit</Button>
> ```
> Variants: default | destructive | outline | secondary | ghost | link
```

### Step 6 — Permission Gate

```markdown
---

## Permission Gate

✅ **Phase FE-N scope complete.**

Verified acceptance criteria:
- [ ] `npm run dev` → no errors in console
- [ ] [feature criterion with exact test/curl command]

**Next — Phase FE-N+1**: [one-line summary]

Reply with **"proceed"** to start Phase FE-N+1, or describe what to adjust first.
```

---

## Quality Checklist

Before publishing any ExecPlan:
- [ ] All steps have a concrete file path
- [ ] All steps have a verify command + expected output
- [ ] All backend endpoint shapes are embedded (not linked)
- [ ] TypeScript interfaces defined before components that use them
- [ ] Phase ends with permission gate
- [ ] No step says "the reader can decide" — every ambiguity is resolved
