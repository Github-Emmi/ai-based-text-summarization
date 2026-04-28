# ExecPlan Template

Copy this skeleton for each new phase. Fill in every section — do not leave placeholder text.

---

```markdown
# ExecPlan — Phase N: [Phase Name]

**Date**: YYYY-MM-DD  
**Agent**: AI-BASED-TEXT-SUMMARIZATION  
**Approved by**: [user handle]  
**Depends on**: Phase N-1 complete (verified: [criterion met])

---

## 1. Repository Summary

**Last inventoried**: YYYY-MM-DD

### Phase Status
| Phase | Name | Status | Evidence |
|-------|------|--------|---------|
| 0 | Repo & Env Bootstrap | complete | `git remote -v` shows origin |
| 1 | Foundation | [status] | [evidence] |
| 2 | Core Summarization | [status] | [evidence] |
| 3 | Advanced Features | [status] | [evidence] |
| 4 | Production Hardening | [status] | [evidence] |

### Files Present (verified with search/read)
- `backend/app/main.py` — [purpose]
- `backend/docker/Dockerfile` — [purpose]
- *(list every file in scope for this phase)*

### Files Missing (documented but absent)
- `backend/app/services/summarizer.py` — needed in Phase 2 Step 3
- *(list each with the step that will create it)*

### Contradictions (docs say X, code does Y)
- None detected **OR**
- `docs/06-api-design.md` documents `POST /api/v1/summarize/text` but `app/api/v1/summarize.py` has no route for it

---

## 2. Critical Findings

*(Ordered CRITICAL → HIGH → MEDIUM → LOW. Omit LOW if > 10 findings.)*

| Severity | File | Issue | Impact | Fix in Step |
|----------|------|-------|--------|-------------|
| CRITICAL | `backend/app/main.py` | File missing | App cannot start | Step 3 |
| HIGH | `backend/.env.example` | File missing | Devs have no config template | Step 1 |
| MEDIUM | `backend/app/core/config.py` | `DB_POOL_SIZE` hardcoded to 5 | Cannot tune for production | Step 2 |

*(If no findings: "No blocking findings. Proceeding with Phase N scope.")*

---

## 3. Phase Plan

| Phase | Name | Key Deliverable | Status | Acceptance Criteria |
|-------|------|-----------------|--------|---------------------|
| 0 | Repo & Env Bootstrap | GitHub repo, venv, .gitignore | [status] | `git remote -v` shows origin |
| 1 | Foundation | `/health` → 200, DB pool connected | [status] | `curl localhost:8000/health` → `{"status":"ok"}` |
| 2 | Core Summarization | `POST /api/v1/summarize/text` returns summary | [status] | `pytest tests/integration/test_summarize_text.py` passes |
| 3 | Advanced Features | Auth + chat + keywords + PDF export | [status] | `pytest tests/integration/` passes |
| 4 | Production Hardening | Render deploy live at public URL | [status] | `curl https://....onrender.com/health` → `{"status":"ok"}` |

---

## 4. Phase N Scope — [Phase Name]

> **Assumption**: [State any assumption this phase relies on. E.g., "Phase 0 is complete and `origin` remote is set."]

### Step 1 — [Action Verb] [Subject]

**File**: `backend/path/to/file.py`  
**Why**: [One sentence — why this file, why now.]

> **Knowledge**: [Embed any library/API knowledge the executing agent needs. Example:]
> `asyncpg.create_pool()` accepts `min_size` and `max_size` keyword args. It returns an `asyncpg.Pool`
> object that must be stored and passed to `pool.acquire()` as a context manager.

```python
# Full file content or minimal diff that makes the step testable
# NEVER use "..." or "# existing code" placeholders
# The executing agent must be able to copy this and have a working file

[complete file content here]
```

**Verify**:
```bash
cd backend
source venv/bin/activate
[exact command]
```
Expected output:
```
[key lines from expected output — enough to confirm success]
```

---

### Step 2 — [Action Verb] [Subject]

**File**: `backend/path/to/another_file.py`  
**Why**: [One sentence.]

*(Repeat structure for every step in the phase.)*

---

### Step N — Run Phase Acceptance Tests

```bash
cd backend
source venv/bin/activate
pytest [specific test files for this phase] -v
```
Expected output:
```
collected N items

tests/[...]/test_something.py::test_name PASSED
...
N passed in X.XXs
```

If tests fail: check [specific thing] first, then [second thing].

---

## Permission Gate

✅ **Phase N scope complete.**

Verified acceptance criteria:
- [ ] [Criterion 1]: `[exact command]` → `[expected output snippet]`
- [ ] [Criterion 2]: `[exact command]` → `[expected output snippet]`
- [ ] No regressions: `pytest [previous phase tests] -v` → all pass

**Next — Phase N+1**: [One-line summary of what Phase N+1 builds.]

Reply with **"proceed"** to start Phase N+1, or describe what to adjust first.
```
