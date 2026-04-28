# Phase Quality Checklist

Run this checklist on every ExecPlan before saving it. Every item must be ✅ before the plan is handed to an executing agent.

---

## Section 1 — Discovery Completeness

- [ ] Agent file (`.github/agents/AI-BASED-TEXT-SUMMARIZATION.agent.md`) was read in full
- [ ] All 11 `docs/` files were read (00 through 11)
- [ ] Every file listed in `docs/04-project-structure.md` for this phase was searched for (not assumed)
- [ ] Repository Summary section lists files as **present** only if `search` or `read` confirmed they exist
- [ ] Contradictions section is populated (even if it says "None detected")

---

## Section 2 — Gap Analysis Quality

- [ ] Every CRITICAL finding blocks the phase acceptance criteria (if it doesn't, downgrade to HIGH)
- [ ] Every finding has a specific file path (no "somewhere in the codebase")
- [ ] Every finding has a "Fix in Step" reference to where it is resolved
- [ ] No finding says "refactor" or "improve" without a concrete, testable outcome

---

## Section 3 — Step Completeness

For every step in Phase N Scope:

- [ ] The step has a **File** target (never "the service layer")
- [ ] The step has a **Why** sentence explaining timing (why this step, why now)
- [ ] All library/API knowledge needed is embedded in a **Knowledge** block — no external URL links
- [ ] The implementation block contains **complete file content** — no `...`, no `# existing code`, no `pass` bodies left unexplained
- [ ] The **Verify** block has an exact bash command (not "run the app")
- [ ] The **Expected output** block shows the actual lines the agent should see (not "output will show success")
- [ ] The step does not do two unrelated things — split into separate steps if needed

---

## Section 4 — Ambiguity Resolution

- [ ] No step says "choose an appropriate X" — the X is named
- [ ] No step says "handle errors" — the exact exception classes and HTTP status codes are specified
- [ ] No step says "set up authentication" — the exact JWT claims, TTL, and header format are stated
- [ ] No step says "configure the database" — the exact pool settings and DSN format are specified
- [ ] All Pydantic model fields have explicit types, `min_length`, `max_length`, and `default` values

---

## Section 5 — Evidence Blocks

- [ ] Every step that creates a file has a verify block
- [ ] Every step that starts a service has a verify block with the expected health endpoint response
- [ ] Every step that adds a route has a `curl` example with the exact expected JSON response
- [ ] Every step that runs migrations has `alembic current` as the verify command and shows the expected revision
- [ ] The final step runs the phase acceptance tests and shows expected pytest output

---

## Section 6 — Phase Boundary Discipline

- [ ] The plan implements ONLY the steps documented in the approved phase in `docs/00-project-overview.md`
- [ ] No step creates a file that belongs to a future phase (check against `docs/04-project-structure.md`)
- [ ] No step installs a package only needed in a future phase
- [ ] The permission gate is present and uses the exact required wording

---

## Section 7 — Security

- [ ] No secrets, API keys, or passwords appear in any implementation block (only `settings.X` or env var references)
- [ ] All DB queries use parameterized form (`$1`, `$2` — not f-strings)
- [ ] File upload steps include MIME type validation AND max-size enforcement
- [ ] The `.env.example` file (if created in this phase) contains placeholder values only
- [ ] No `DEBUG=true` or `SECRET_KEY=dev` values appear in any file committed to git

---

## Section 8 — Plan Self-Containment

The following test: give the plan document to an agent with zero context. It should be able to:

- [ ] Know exactly which Python version to use (stated in the plan or in an embedded knowledge block)
- [ ] Know the exact `pip install` commands for every new dependency introduced in this phase
- [ ] Know the exact `alembic` commands to run, in order
- [ ] Know exactly what `docker-compose up -d` starts and on which ports
- [ ] Know the exact acceptance criteria without reading any other document

If any of these fail, add the missing information to the plan before proceeding.

---

## Common Failure Modes Reference

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Agent says "I'll implement a summarizer" and writes a stub | Step said "implement summarization service" without specifying AI client routing | Add the full `app/ai/router.py` content to the step |
| Agent uses `psycopg2` instead of `asyncpg` | No knowledge block specifying the DB driver | Add: "Use asyncpg, not psycopg2 or SQLAlchemy async" |
| Agent writes synchronous route handlers | No explicit instruction to use `async def` | Add: "All route handlers and service methods must be `async def`" |
| Migration fails on `alembic upgrade head` | `env.py` not configured to use app Settings | Add the full `alembic/env.py` content to the Alembic setup step |
| Agent adds `import *` in `__init__.py` | No instruction on import patterns | Add the exact `__init__.py` contents for each new package |
| Tests fail with "fixture 'db' not found" | `conftest.py` not created before test steps | Reorder steps — `conftest.py` must precede first test file |
| Docker build fails | `.dockerignore` missing — venv/ copied into image | Add `.dockerignore` creation as an explicit step |
