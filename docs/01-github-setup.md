# 01 — GitHub Repository Setup

## Overview

This guide walks through creating a new remote GitHub repository, configuring a license and README, and linking it to the local workspace. Run all commands from the project root: `/Volumes/EmmiDev256G/Projects/AI-Based-Text-Summarization`.

**Prerequisites**: `git` and `gh` (GitHub CLI) must be installed and authenticated.

---

## Step 1 — Verify Prerequisites

```bash
# Check git version (requires 2.30+)
git --version

# Check GitHub CLI version and auth status
gh --version
gh auth status
```

Expected output for auth status:
```
✓ Logged in to github.com as <your-username>
✓ Git operations for github.com configured to use https protocol
```

If not authenticated:
```bash
gh auth login
# Choose: GitHub.com → HTTPS → Login with a web browser
```

---

## Step 2 — Initialize Local Git Repository

```bash
# Navigate to project root
cd /Volumes/EmmiDev256G/Projects/AI-Based-Text-Summarization

# Initialize git
git init

# Set default branch name to main
git branch -M main
```

---

## Step 3 — Create `.gitignore`

Create `.gitignore` at the project root before the first commit so no secrets or compiled files are ever tracked:

```bash
cat > .gitignore << 'EOF'
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

# Alembic
# (keep alembic/ folder but not compiled artifacts)
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
EOF
```

---

## Step 4 — Create `README.md`

```bash
cat > README.md << 'EOF'
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

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

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
EOF
```

---

## Step 5 — Create GitHub Repository via CLI

```bash
# Create a public repo with MIT license on GitHub
# --source=. links the remote to the current local directory
gh repo create ai-based-text-summarization \
  --public \
  --description "Production-ready FastAPI backend for AI-powered text and PDF summarization" \
  --license mit \
  --source=. \
  --remote=origin \
  --push
```

> **What this does**:
> - Creates `ai-based-text-summarization` under your GitHub account
> - Adds `MIT` license file (`LICENSE`)
> - Sets `origin` remote to the new repo
> - Pushes the current `main` branch

Verify the remote was added:
```bash
git remote -v
```

Expected:
```
origin  https://github.com/<your-username>/ai-based-text-summarization.git (fetch)
origin  https://github.com/<your-username>/ai-based-text-summarization.git (push)
```

---

## Step 6 — Make the Initial Commit

If you ran `--push` in Step 5, your initial commit was already pushed. Otherwise:

```bash
# Stage all files
git add .

# Verify what will be committed (check .env is NOT listed)
git status

# Commit
git commit -m "chore: initial project scaffold with docs and agent"

# Push to GitHub
git push -u origin main
```

> **Security check**: Confirm `.env` is NOT in `git status` output. If it appears, run `git rm --cached .env` before committing.

---

## Step 7 — Configure Branch Protection (Recommended)

```bash
# Require pull request reviews before merging to main
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks=null \
  --field enforce_admins=false \
  --field "required_pull_request_reviews[required_approving_review_count]=1" \
  --field restrictions=null
```

Or configure via GitHub UI: **Settings → Branches → Add branch protection rule → main**.

---

## Step 8 — Add GitHub Secrets for CI/CD (Later)

When you set up GitHub Actions (Phase 4):

```bash
# Add OpenAI API key as a secret
gh secret set OPENAI_API_KEY --body "sk-..."

# Add Render deploy hook
gh secret set RENDER_DEPLOY_HOOK_URL --body "https://api.render.com/deploy/..."
```

---

## Repository Naming Conventions

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code — protected |
| `develop` | Integration branch for features |
| `feat/<name>` | Feature branches |
| `fix/<name>` | Bug fix branches |
| `chore/<name>` | Infrastructure, docs, tooling |

---

## Verification Checklist

- [ ] `git remote -v` shows the correct `origin` URL
- [ ] GitHub repo page is visible at `https://github.com/<username>/ai-based-text-summarization`
- [ ] `LICENSE` file (MIT) is visible in the repo
- [ ] `README.md` renders correctly on the GitHub repo page
- [ ] `.env` is NOT tracked (run `git ls-files | grep .env` — should return nothing)
- [ ] `docs/` folder is visible in the repo
- [ ] `.github/agents/AI-BASED-TEXT-SUMMARIZATION.agent.md` is visible in the repo
