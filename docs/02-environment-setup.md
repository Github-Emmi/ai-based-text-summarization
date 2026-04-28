# 02 — Environment Setup

## Overview

This guide covers all prerequisites, Python virtual environment creation, Docker setup, and first-run validation. Follow this before implementing any phase.

---

## 1. Prerequisites

### 1.1 — Check Python Version

The backend requires Python **3.10 or higher**.

```bash
python3 --version
# Expected: Python 3.10.x or 3.11.x or 3.12.x
```

If Python 3.10+ is not available (macOS):
```bash
brew install python@3.11
# Then use python3.11 explicitly, or symlink:
echo 'export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
python3 --version
```

### 1.2 — Check Git

```bash
git --version
# Expected: git version 2.30+
```

### 1.3 — Check Docker

```bash
docker --version
# Expected: Docker version 24+

docker compose version
# Expected: Docker Compose version v2.x
```

If Docker is not installed: https://docs.docker.com/desktop/install/mac-install/

### 1.4 — Check GitHub CLI

```bash
gh --version
# Expected: gh version 2.x

gh auth status
# Expected: Logged in to github.com
```

Install if missing:
```bash
brew install gh
gh auth login
```

---

## 2. Create the `backend/` Directory

All backend source lives under `backend/`. This keeps the repo root clean for docs, CI config, and the agent file.

```bash
# From the project root
mkdir backend
cd backend
```

---

## 3. Create Python Virtual Environment

```bash
# Inside backend/
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Verify the correct python is active
which python
# Expected: .../backend/venv/bin/python

python --version
# Expected: Python 3.10+ (matches your system python3)
```

> **Important**: Always activate the venv before running any `pip`, `pytest`, `uvicorn`, or `alembic` commands.

Deactivate when done:
```bash
deactivate
```

---

## 4. Environment Variables

### 4.1 — `.env.example` (committed to git)

This file documents all required variables. It is safe to commit — it contains **no real values**.

```bash
# backend/.env.example will be created in Phase 1 scaffolding.
# It will contain:

# Application
ENVIRONMENT=development
DEBUG=true
APP_NAME=AI-Based Text Summarization
APP_VERSION=1.0.0
SECRET_KEY=change-this-to-a-long-random-string-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DB_USER=summarize_user
DB_PASSWORD=summarize_pass
DB_HOST=localhost
DB_PORT=5432
DB_NAME=summarize_db
DB_POOL_MIN_SIZE=2
DB_POOL_MAX_SIZE=10

# AI Services
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=1024
OPENAI_TEMPERATURE=0.3
HUGGINGFACE_MODEL=facebook/bart-large-cnn
USE_LOCAL_MODEL=false
HUGGINGFACE_API_TOKEN=hf-your-token-here

# File Upload
MAX_UPLOAD_SIZE_MB=20
UPLOAD_DIR=uploads/

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30

# Logging
LOG_LEVEL=INFO
```

### 4.2 — Create `.env` (local only, never committed)

```bash
# Inside backend/
cp .env.example .env

# Edit .env with real values
nano .env
# or: code .env
```

> **Security rule**: `.env` is in `.gitignore`. Never commit it. Verify with:
> ```bash
> git ls-files backend/.env
> # Should return nothing
> ```

---

## 5. Docker Setup

Docker runs the full stack (FastAPI + PostgreSQL + Adminer) without installing PostgreSQL locally.

### 5.1 — Verify Docker Daemon Is Running

```bash
docker info | grep "Server Version"
# If error: open Docker Desktop app first
```

### 5.2 — `docker-compose.yml` Location

The compose file lives at `backend/docker-compose.yml` (created in Phase 1).

### 5.3 — Start the Full Stack

```bash
cd backend
docker-compose up -d
```

### 5.4 — Verify All Services Are Healthy

```bash
docker-compose ps
```

Expected:
```
NAME                STATUS          PORTS
backend-app-1       running         0.0.0.0:8000->8000/tcp
backend-db-1        running (healthy) 0.0.0.0:5432->5432/tcp
backend-adminer-1   running         0.0.0.0:8080->8080/tcp
```

### 5.5 — Service Access

| Service | URL | Credentials |
|---------|-----|-------------|
| FastAPI | http://localhost:8000 | — |
| Swagger UI | http://localhost:8000/docs | — |
| ReDoc | http://localhost:8000/redoc | — |
| Health Check | http://localhost:8000/health | — |
| Adminer (DB UI) | http://localhost:8080 | System: PostgreSQL, Server: db, User: from .env |

### 5.6 — Common Docker Commands

```bash
# View real-time logs for the app container
docker-compose logs -f app

# Stop all services (keeps data volumes)
docker-compose down

# Stop and delete all volumes (wipes the database)
docker-compose down -v

# Rebuild the app image after code/dependency changes
docker-compose build app
docker-compose up -d

# Open a shell inside the app container
docker-compose exec app bash

# Open a psql shell inside the database container
docker-compose exec db psql -U summarize_user -d summarize_db
```

---

## 6. Local Development (Without Docker)

Use this mode when you want fast iteration without rebuilding Docker images.

**Requirements**: PostgreSQL must be running locally or via Docker (db service only).

```bash
# Start only the database and adminer (not the app)
docker-compose up -d db adminer

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or using the convenience script (created in Phase 1):
```bash
python main.py
```

---

## 7. Install Python Dependencies

```bash
# Inside backend/, with venv activated
pip install -r requirements.txt

# Verify key packages installed
pip show fastapi uvicorn asyncpg sqlalchemy alembic openai pdfplumber
```

To update the requirements file after adding a new package:
```bash
pip install <new-package>
pip freeze > requirements.txt
```

> **Note**: Use `requirements.txt` for deployment. Do not use `pyproject.toml` unless explicitly migrating to that pattern.

---

## 8. Run Database Migrations

After the database is running:

```bash
# Activate venv, inside backend/
source venv/bin/activate

# Apply all pending migrations
alembic upgrade head

# Check current revision
alembic current

# View migration history
alembic history
```

---

## 9. Environment Validation Checklist

Run this after completing setup to confirm everything is wired correctly:

```bash
# 1. Health endpoint responds
curl http://localhost:8000/health
# Expected: {"status": "ok", "environment": "development", "version": "1.0.0"}

# 2. Database is reachable from the app
curl http://localhost:8000/health/db
# Expected: {"status": "ok", "database": "connected"}

# 3. Swagger UI loads
open http://localhost:8000/docs

# 4. Adminer UI loads
open http://localhost:8080
```

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `docker-compose up` fails — port 5432 in use | Local PostgreSQL already running | `brew services stop postgresql` or change `DB_PORT` in `.env` |
| `ModuleNotFoundError` | venv not activated | `source venv/bin/activate` |
| `alembic upgrade head` fails — connection refused | DB container not healthy yet | Wait 10s, retry; check `docker-compose logs db` |
| OpenAI `AuthenticationError` | Missing or wrong API key | Check `OPENAI_API_KEY` in `.env` |
| `uvicorn` import error | Wrong Python / missing deps | Verify `which python` points to venv, then `pip install -r requirements.txt` |
