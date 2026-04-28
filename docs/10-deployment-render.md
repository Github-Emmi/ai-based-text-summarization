# 10 — Deployment to Render

## Overview

The production backend runs on **Render** using a Docker Web Service for the FastAPI app and Render's managed PostgreSQL for the database. Render auto-deploys on push to `main` and provides zero-downtime rolling deployments.

---

## Prerequisites

Before deploying:
- [ ] All Phase 1-3 tests pass: `pytest --cov=app --cov-fail-under=80`
- [ ] Docker image builds successfully locally: `docker build -f docker/Dockerfile -t ai-summarize:latest .`
- [ ] `.env.example` is committed with all required variables documented
- [ ] `DEBUG=false` and `ENVIRONMENT=production` in Render env vars
- [ ] A new `SECRET_KEY` value generated (never use the dev key in production)
- [ ] `OPENAI_API_KEY` is a real, active key

---

## 1. Create Render Account

1. Go to https://render.com and sign up with GitHub
2. Authorize the GitHub integration to access your `ai-based-text-summarization` repo

---

## 2. Create Render PostgreSQL Database

1. In Render Dashboard → **New** → **PostgreSQL**
2. Configure:
   - **Name**: `ai-text-summarization-db`
   - **Region**: Oregon (US West) — or closest to your users
   - **Plan**: Starter ($7/mo) — for always-on, no sleep
   - **PostgreSQL Version**: 15
3. Click **Create Database**
4. After creation, copy the **Internal Database URL** — looks like:
   ```
   postgresql://user:pass@dpg-xxx-a.oregon-postgres.render.com/summarize_db_xxx
   ```
   This URL is used as `DATABASE_URL` in the web service environment variables.

---

## 3. Create `render.yaml`

Place `render.yaml` in the **repo root** (not inside `backend/`). Render auto-detects this file.

```yaml
services:
  - type: web
    name: ai-text-summarization-api
    region: oregon
    plan: starter
    runtime: docker
    dockerfilePath: ./backend/docker/Dockerfile
    dockerContext: ./backend
    healthCheckPath: /health
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: "false"
      - key: APP_NAME
        value: AI-Based Text Summarization
      - key: APP_VERSION
        value: "1.0.0"
      - key: DATABASE_URL
        fromDatabase:
          name: ai-text-summarization-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true         # Render auto-generates a secure secret
      - key: ALGORITHM
        value: HS256
      - key: ACCESS_TOKEN_EXPIRE_MINUTES
        value: "30"
      - key: REFRESH_TOKEN_EXPIRE_DAYS
        value: "7"
      - key: DB_POOL_MIN_SIZE
        value: "2"
      - key: DB_POOL_MAX_SIZE
        value: "10"
      - key: CORS_ORIGINS
        value: https://your-frontend-domain.com
      - key: RATE_LIMIT_PER_MINUTE
        value: "30"
      - key: MAX_UPLOAD_SIZE_MB
        value: "20"
      - key: LOG_LEVEL
        value: INFO
      - key: USE_LOCAL_MODEL
        value: "false"
      - key: OPENAI_MODEL
        value: gpt-4o-mini
      - key: OPENAI_MAX_TOKENS
        value: "1024"
      - key: OPENAI_TEMPERATURE
        value: "0.3"
      # These must be set manually in Render Dashboard (secrets):
      # OPENAI_API_KEY
      # HUGGINGFACE_API_TOKEN

databases:
  - name: ai-text-summarization-db
    plan: starter
    region: oregon
    databaseName: summarize_db
    user: summarize_user
    postgresMajorVersion: 15
```

> **Security**: `OPENAI_API_KEY` and `HUGGINGFACE_API_TOKEN` must be added manually in the Render Dashboard under **Environment → Secret Files** — never hardcode them in `render.yaml`.

---

## 4. Production `Dockerfile` (`backend/docker/Dockerfile`)

Multi-stage build: `builder` installs dependencies, `runtime` runs the app as a non-root user.

```dockerfile
# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a local dir for copying
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create uploads directory with correct permissions
RUN mkdir -p uploads && chown appuser:appgroup uploads

# Switch to non-root user
USER appuser

EXPOSE 8000

# Use entrypoint script to run migrations then start the server
ENTRYPOINT ["./docker/entrypoint.sh"]
```

### `backend/docker/entrypoint.sh`

```bash
#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  --no-access-log
```

Make it executable:
```bash
chmod +x backend/docker/entrypoint.sh
git add backend/docker/entrypoint.sh
```

---

## 5. `docker-compose.yml` (Local Dev — inside `backend/`)

```yaml
version: "3.9"

services:
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./:/app        # bind mount for hot-reload in dev
      - uploads:/app/uploads
    depends_on:
      db:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s

  adminer:
    image: adminer:latest
    ports:
      - "8080:8080"
    depends_on:
      - db

volumes:
  postgres_data:
  uploads:
```

---

## 6. Deploy to Render

### Option A — Automatic (render.yaml)

```bash
# From the repo root
git add render.yaml backend/docker/Dockerfile backend/docker/entrypoint.sh
git commit -m "chore: add Render deployment config"
git push origin main
```

Render detects `render.yaml` on push and auto-creates the services.

### Option B — Manual (Render Dashboard)

1. Render Dashboard → **New** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name**: `ai-text-summarization-api`
   - **Region**: Oregon
   - **Branch**: `main`
   - **Runtime**: Docker
   - **Dockerfile Path**: `./backend/docker/Dockerfile`
   - **Docker Context**: `./backend`
4. Set environment variables (see Step 3 list above)
5. Click **Create Web Service**

---

## 7. Add Secrets in Render Dashboard

After the service is created:

1. Go to Web Service → **Environment**
2. Add:
   - `OPENAI_API_KEY` = `sk-your-real-key`
   - `HUGGINGFACE_API_TOKEN` = `hf-your-real-token`
3. Click **Save Changes** — Render automatically redeploys

---

## 8. Configure DATABASE_URL for asyncpg

Render provides `DATABASE_URL` as a full Postgres URL. asyncpg requires this format:
```
postgresql://user:pass@host:5432/dbname
```

Not `postgresql+asyncpg://` (that's SQLAlchemy format). Verify in `app/core/config.py`:

```python
@property
def database_url(self) -> str:
    # Render provides DATABASE_URL — use it directly
    if self.DATABASE_URL:
        return self.DATABASE_URL.replace("postgres://", "postgresql://")
    return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
```

---

## 9. Verify Production Deploy

```bash
# Check health endpoint
curl https://ai-text-summarization-api.onrender.com/health

# Expected:
# {"status": "ok", "environment": "production", "version": "1.0.0"}

# Check DB health
curl https://ai-text-summarization-api.onrender.com/health/db

# Open Swagger UI in browser
open https://ai-text-summarization-api.onrender.com/docs
```

---

## 10. Monitoring & Logs

```bash
# View live logs via Render CLI
render logs --service ai-text-summarization-api --tail

# Or view in Render Dashboard:
# Web Service → Logs tab
```

Render provides:
- **Metrics**: CPU, memory, request count, response time
- **Events**: Deploy history, health check status
- **Alerts**: Configure email/Slack alerts for service health

---

## Render Plan Reference

| Service | Plan | Cost | Notes |
|---------|------|------|-------|
| Web Service | Starter | $7/mo | No sleep, 512MB RAM, 0.5 vCPU |
| PostgreSQL | Starter | $7/mo | 1GB storage, daily backups |
| **Total** | | **$14/mo** | Production-ready minimum |

> **Free tier warning**: The Render free tier sleeps after 15 minutes of inactivity (cold start ~30s). Use Starter for a production deployment.

---

## Rollback

To roll back to a previous deployment:
1. Render Dashboard → Web Service → **Events**
2. Find the last good deploy
3. Click **Redeploy**

Or via `render.yaml` — revert the commit and push.

---

## GitHub Actions Auto-Deploy (Phase 4 — Optional)

Add to `.github/workflows/ci.yml`:

```yaml
- name: Trigger Render Deploy
  if: github.ref == 'refs/heads/main' && success()
  run: |
    curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}"
```

Set `RENDER_DEPLOY_HOOK_URL` in GitHub repo secrets (get from Render Dashboard → Web Service → Settings → Deploy Hook).
