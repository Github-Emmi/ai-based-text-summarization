# ExecPlan — Phase 0: Repo & Environment Bootstrap

**Date**: 2026-04-29  
**Agent**: AI-BASED-TEXT-SUMMARIZATION  
**Approved by**: User (confirmed "Yes, start execution with the first phase")  
**Depends on**: Nothing — this is the first phase.

---

## 1. Repository Summary

**Last inventoried**: 2026-04-29

### Phase Status

| Phase | Name | Status | Evidence |
|-------|------|--------|---------|
| 0 | Repo & Env Bootstrap | **in-progress** | No git repo yet; `git status` returns `fatal: not a git repository` |
| 1 | Foundation | not-started | `backend/` does not exist |
| 2 | Core Summarization | not-started | No application code |
| 3 | Advanced Features | not-started | No application code |
| 4 | Production Hardening | not-started | No application code |

### Files Present (verified by `find` on 2026-04-29)

```
.github/agents/AI-BASED-TEXT-SUMMARIZATION.agent.md  ← specialist agent ✅
.github/skills/exec-plan/SKILL.md                    ← exec-plan skill ✅
.github/skills/exec-plan/references/execplan-template.md ✅
.github/skills/exec-plan/references/phase-checklist.md  ✅
docs/00-project-overview.md  ✅
docs/01-github-setup.md      ✅
docs/02-environment-setup.md ✅
docs/03-architecture.md      ✅
docs/04-project-structure.md ✅
docs/05-database-schema.md   ✅
docs/06-api-design.md        ✅
docs/07-ai-integration.md    ✅
docs/08-advanced-features.md ✅
docs/09-testing-strategy.md  ✅
docs/10-deployment-render.md ✅
docs/11-security-checklist.md ✅
```

### Files Missing (documented in `docs/04-project-structure.md` but absent)

Every file and directory in the `backend/` tree is missing — no Python code exists yet. This is expected; Phase 0 only bootstraps the repo shell. The backend scaffold is Phase 1.

| Missing Path | Created In |
|---|---|
| `backend/` (directory) | Phase 0 Step 4 |
| `README.md` | Phase 0 Step 3 |
| `.gitignore` | Phase 0 Step 2 |
| `LICENSE` | Phase 0 Step 5 (via `gh repo create --license mit`) |
| `backend/venv/` | Phase 0 Step 4 |
| All `backend/app/**` | Phase 1 |
| `backend/docker-compose.yml` | Phase 1 |
| `backend/alembic/` | Phase 1 |

### Contradictions

None detected. Docs describe Phase 0 as "Repo & Environment Bootstrap" and the repo is precisely at pre-init state.

---

## 2. Critical Findings

| Severity | File | Issue | Impact | Fix in Step |
|----------|------|-------|--------|-------------|
| CRITICAL | (repo root) | `git init` not run — no git repository exists | Cannot commit, cannot push, cannot track history | Step 1 |
| CRITICAL | `.gitignore` | Missing — if files are committed before `.gitignore` exists, secrets and compiled files can be tracked | Potential secret leak in git history | Step 2 |
| HIGH | `README.md` | Missing — `gh repo create --push` requires at least one commit | Push will fail without an initial commit | Step 3 |
| HIGH | `backend/` | Directory does not exist | No Python environment possible | Step 4 |
| MEDIUM | `LICENSE` | Missing locally — `gh repo create --license mit` will create it on the remote and merge into local | MIT not visible in local checkout until push + pull completes | Step 5 |

---

## 3. Phase Plan

| Phase | Name | Key Deliverable | Status | Acceptance Criteria |
|-------|------|-----------------|--------|---------------------|
| **0** | **Repo & Env Bootstrap** | GitHub repo + local git + venv | **in-progress** | `git remote -v` shows `origin`, `python --version` inside `backend/venv` returns 3.10+ |
| 1 | Foundation | `/health` → 200, DB pool connected | not-started | `curl http://localhost:8000/health` → `{"status":"ok","version":"1.0.0"}` |
| 2 | Core Summarization | `POST /api/v1/summarize/text` returns summary | not-started | `pytest tests/integration/test_summarize_text.py -v` passes |
| 3 | Advanced Features | Auth + chat + keywords + PDF export | not-started | `pytest tests/integration/` passes (all tests) |
| 4 | Production Hardening | Render deploy live at public URL | not-started | `curl https://<app>.onrender.com/health` → `{"status":"ok"}` |

---

## 4. Phase 0 Scope — Repo & Environment Bootstrap

> **Assumption**: `gh auth status` confirms `Github-Emmi` is logged in via HTTPS with `repo`, `workflow`, `gist`, `read:org` scopes. No additional authentication steps are needed.
>
> **Assumption**: Python 3.14.3 is installed at `/usr/local/bin/python3` (confirmed by `python3 --version` returning `Python 3.14.3`). This satisfies the ≥ 3.10 requirement.
>
> **Assumption**: All commands are run from the project root: `/Volumes/EmmiDev256G/Projects/AI-Based-Text-Summarization`.

---

### Step 1 — Initialize Local Git Repository

**Why**: Nothing can be tracked, committed, or pushed until `git init` runs. The branch must be named `main` to match GitHub's default and the Render deploy configuration.

```bash
cd /Volumes/EmmiDev256G/Projects/AI-Based-Text-Summarization
git init
git branch -M main
```

**Verify**:
```bash
git status
```
Expected output:
```
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.github/
	docs/
```

---

### Step 2 — Create `.gitignore` at Repo Root

**Why**: `.gitignore` must exist and be committed **before** any other file is added to the index. If it is added after `backend/.env` is already tracked, the env file stays in git history forever.

> **Knowledge**: `git add` respects `.gitignore` only for files that have **never** been staged. If you accidentally stage `.env` before `.gitignore` is committed, use `git rm --cached backend/.env` to untrack it while keeping the local file.

```
.gitignore content (write to repo root):

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg
*.egg-info/
dist/
build/
.eggs/

# Virtual environment
venv/
.venv/
env/
ENV/

# Environment variables — NEVER commit .env
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# macOS
.DS_Store
.AppleDouble
.LSOverride

# pytest / coverage
.pytest_cache/
.coverage
htmlcov/
coverage.xml

# Compiled Python
*.pyc

# Docker
docker-compose.override.yml

# Logs
*.log
logs/

# Uploads (local dev)
backend/uploads/

# Jupyter
.ipynb_checkpoints/
```

**Verify**:
```bash
git check-ignore -v backend/.env
```
Expected output (once `backend/.env` exists in Phase 1):
```
.gitignore:11:.env	backend/.env
```
For now, verify the file is staged correctly:
```bash
git add .gitignore
git status
```
Expected output:
```
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
	new file:   .gitignore
```

---

### Step 3 — Create `README.md`

**Why**: `gh repo create --push` pushes the current HEAD. HEAD requires at least one commit, which requires at least one staged file. `README.md` is the canonical first file. It also renders on the GitHub repo homepage.

```
README.md content (write to repo root):

# AI-Based Text Summarization Platform

A production-ready FastAPI backend for AI-powered text and PDF summarization using OpenAI GPT-4o-mini and HuggingFace Transformers.

## Features

- Text and PDF summarization (OpenAI GPT-4o-mini + HuggingFace BART fallback)
- JWT user authentication
- Chat with document (conversation history persisted in PostgreSQL)
- Keyword extraction (KeyBERT)
- Multi-language support
- Export summary as PDF
- Async FastAPI with asyncpg connection pooling
- Docker + Docker Compose for full local environment
- Deployable to Render

## Quick Start

See [docs/02-environment-setup.md](docs/02-environment-setup.md) for detailed setup instructions.

    cd backend
    cp .env.example .env
    # Edit .env with your API keys
    docker-compose up -d

API available at: http://localhost:8000
Swagger UI: http://localhost:8000/docs

## Documentation

| Doc | Description |
|-----|-------------|
| [Project Overview](docs/00-project-overview.md) | Goals, stack, deliverables |
| [GitHub Setup](docs/01-github-setup.md) | Repository creation guide |
| [Environment Setup](docs/02-environment-setup.md) | Prerequisites and local dev |
| [Architecture](docs/03-architecture.md) | System design and data flow |
| [Project Structure](docs/04-project-structure.md) | Folder and file layout |
| [Database Schema](docs/05-database-schema.md) | Tables, relationships, migrations |
| [API Design](docs/06-api-design.md) | Endpoints and schemas |
| [AI Integration](docs/07-ai-integration.md) | OpenAI and HuggingFace integration |
| [Advanced Features](docs/08-advanced-features.md) | Auth, chat, export, keywords |
| [Testing Strategy](docs/09-testing-strategy.md) | Test structure and commands |
| [Render Deployment](docs/10-deployment-render.md) | Production deployment guide |
| [Security Checklist](docs/11-security-checklist.md) | OWASP hardening checklist |

## License

MIT
```

---

### Step 4 — Create `backend/` Directory and Python Virtual Environment

**Why**: All application code lives under `backend/`. The virtual environment is created here so `pip`, `pytest`, and `uvicorn` are isolated to this project and never pollute the system Python.

> **Knowledge**: `python3 -m venv venv` creates a self-contained Python environment at `backend/venv/`. After activation, `python` and `pip` resolve to the venv binaries, not the system ones. Always activate the venv before running any project commands.
>
> **Knowledge**: The venv directory is covered by the `.gitignore` rule `venv/` — it is never committed. Each developer runs `python3 -m venv venv` once after cloning.

```bash
mkdir backend
cd backend
python3 -m venv venv
source venv/bin/activate
```

**Verify**:
```bash
which python
python --version
```
Expected output:
```
/Volumes/EmmiDev256G/Projects/AI-Based-Text-Summarization/backend/venv/bin/python
Python 3.14.3
```

Return to project root:
```bash
cd ..
```

---

### Step 5 — Stage All Files and Create Initial Commit

**Why**: `gh repo create --push` requires a local HEAD commit to push. We commit all documentation, agent files, skill files, `.gitignore`, and `README.md` in a single initial commit.

```bash
# Stage everything (venv/ is excluded by .gitignore)
git add .

# Verify nothing sensitive is staged
git status
```

Expected status (condensed — all paths are docs/.github/README/.gitignore):
```
On branch main

No commits yet

Changes to be committed:
  new file:   .github/agents/AI-BASED-TEXT-SUMMARIZATION.agent.md
  new file:   .github/skills/exec-plan/SKILL.md
  new file:   .github/skills/exec-plan/references/execplan-template.md
  new file:   .github/skills/exec-plan/references/phase-checklist.md
  new file:   .gitignore
  new file:   README.md
  new file:   docs/00-project-overview.md
  ... (all 12 docs files)
  new file:   docs/execplans/phase-0-repo-bootstrap.md
```

**Security check** — confirm `.env` is NOT staged (it doesn't exist yet but verify the rule works):
```bash
git ls-files --others --ignored --exclude-standard | grep "\.env"
# Should return nothing (no .env file exists yet)
```

Create the commit:
```bash
git commit -m "chore: Phase 0 bootstrap — docs, agent, skills, .gitignore, README"
```

Expected output:
```
[main (root-commit) xxxxxxx] chore: Phase 0 bootstrap — docs, agent, skills, .gitignore, README
 N files changed, M insertions(+)
 create mode 100644 .github/agents/AI-BASED-TEXT-SUMMARIZATION.agent.md
 ...
```

---

### Step 6 — Create GitHub Repository and Push

**Why**: `gh repo create --source=. --push` creates the GitHub remote, adds an MIT `LICENSE` file in the remote, sets the `origin` remote on the local repo, and pushes `main` in one command.

> **Knowledge**: When `--license mit` is used with `gh repo create`, GitHub creates the LICENSE file directly in the remote repository. It does NOT add the file to your local directory. After the push, run `git pull origin main` to bring the LICENSE into your local checkout.
>
> **Knowledge**: The GitHub repo name `ai-based-text-summarization` will be created under the authenticated account (`Github-Emmi`). The full remote URL will be `https://github.com/Github-Emmi/ai-based-text-summarization`.

```bash
gh repo create ai-based-text-summarization \
  --public \
  --description "Production-ready FastAPI backend for AI-powered text and PDF summarization" \
  --license mit \
  --source=. \
  --remote=origin \
  --push
```

Expected output:
```
✓ Created repository Github-Emmi/ai-based-text-summarization on GitHub
✓ Added remote https://github.com/Github-Emmi/ai-based-text-summarization.git
✓ Pushed commits to https://github.com/Github-Emmi/ai-based-text-summarization.git
```

**Verify remote**:
```bash
git remote -v
```
Expected output:
```
origin	https://github.com/Github-Emmi/ai-based-text-summarization.git (fetch)
origin	https://github.com/Github-Emmi/ai-based-text-summarization.git (push)
```

---

### Step 7 — Pull LICENSE into Local Checkout

**Why**: `gh repo create --license mit` writes `LICENSE` to the remote only. Pull it so the local repo is in sync and future pushes don't create divergence.

```bash
git pull origin main --allow-unrelated-histories
```

Expected output:
```
From https://github.com/Github-Emmi/ai-based-text-summarization
 * branch            main       -> FETCH_HEAD
Merge made by the 'ort' strategy.
 LICENSE | 21 +++++++++++++++++++++
 1 file changed, 21 insertions(+)
 create mode 100644 LICENSE
```

**Verify**:
```bash
ls LICENSE
cat LICENSE | head -3
```
Expected output:
```
LICENSE
MIT License

Copyright (c) 2026 Github-Emmi
```

---

### Step 8 — Phase 0 Acceptance Tests

**Why**: Confirm every Phase 0 deliverable is in place before requesting permission for Phase 1.

```bash
# 1. Verify git repo is clean and on main
git status

# 2. Verify remote is set
git remote -v

# 3. Verify .gitignore is working (venv is not tracked)
git ls-files backend/venv/ | head -3
# Expected: empty output

# 4. Verify Python venv is functional
source backend/venv/bin/activate
python --version
deactivate

# 5. Verify all docs are committed
git log --oneline | head -3

# 6. Verify LICENSE exists locally
ls LICENSE
```

Expected composite output:
```
On branch main
nothing to commit, working tree clean
---
origin	https://github.com/Github-Emmi/ai-based-text-summarization.git (fetch)
origin	https://github.com/Github-Emmi/ai-based-text-summarization.git (push)
---
(empty — venv is gitignored) ✅
---
Python 3.14.3 ✅
---
xxxxxxx (HEAD -> main, origin/main) Merge remote-tracking branch 'origin/main'
xxxxxxx chore: Phase 0 bootstrap — docs, agent, skills, .gitignore, README
---
LICENSE ✅
```

---

## Permission Gate

✅ **Phase 0 scope complete.**

Verified acceptance criteria:
- [ ] `git remote -v` shows `origin https://github.com/Github-Emmi/ai-based-text-summarization.git`
- [ ] `git status` → `nothing to commit, working tree clean`
- [ ] `source backend/venv/bin/activate && python --version` → `Python 3.14.3`
- [ ] `git ls-files backend/venv/` → empty (venv is gitignored)
- [ ] `ls LICENSE` → `LICENSE` (MIT license present locally)

**Next — Phase 1 — Foundation**: Scaffold `backend/app/`, create `docker-compose.yml` + `Dockerfile`, configure asyncpg pool, implement `GET /health` endpoint, set up Alembic migrations, write `requirements.txt` and `.env.example`.

Reply with **"proceed"** to start Phase 1, or describe what to adjust first.
