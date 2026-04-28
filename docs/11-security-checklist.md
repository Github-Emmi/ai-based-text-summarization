# 11 — Security Checklist

## Overview

This checklist covers OWASP Top 10 mitigations and production hardening requirements. Each item maps to a specific threat, its implementation location, and verification method. Complete all CRITICAL and HIGH items before deploying to production. Review before each major release.

---

## OWASP Top 10 — Mitigation Map

| # | OWASP Category | Threat | Mitigation | Status |
|---|---------------|--------|-----------|--------|
| A01 | Broken Access Control | Users accessing other users' data | JWT + `get_current_user` on all /api/v1/* routes + `user_id` check in repositories | Phase 2 |
| A02 | Cryptographic Failures | Plaintext passwords, exposed secrets | bcrypt cost=12 + .env gitignored + SECRET_KEY rotation | Phase 3 |
| A03 | Injection | SQL injection via user input | asyncpg parameterized queries only — no string-formatted SQL | Phase 1 |
| A04 | Insecure Design | No rate limiting, no input bounds | slowapi rate limiter + Pydantic field validation (min/max) | Phase 4 |
| A05 | Security Misconfiguration | CORS wildcard, debug mode in prod | CORS locked to specific origins + DEBUG=false in production | Phase 1/4 |
| A06 | Vulnerable Components | Outdated dependencies | `pip audit` in CI + pinned `requirements.txt` | Phase 4 |
| A07 | Auth and Session Failures | Long-lived tokens, weak passwords | 30-min access tokens + 7-day refresh rotation + password policy | Phase 3 |
| A08 | Software and Data Integrity | Tampered JWT, unsafe deserialization | HS256 JWT signature verification + Pydantic deserialization only | Phase 3 |
| A09 | Logging and Monitoring Failures | No audit trail, silent errors | Structured JSON logging with request IDs on all routes | Phase 1 |
| A10 | Server-Side Request Forgery | Crafted URLs to internal services | No URL fetching from user input; AI calls only to known endpoints | All phases |

---

## Critical Security Items

### SEC-01 — Secret Key

- [ ] `SECRET_KEY` is at least 32 random bytes
- [ ] Never use the example key (`change-this-to-a-long-random-string-in-production`) in production
- [ ] Rotate by changing `SECRET_KEY` env var + redeploying (all existing tokens invalidated)

**Generate a secure key**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Render**: Use `generateValue: true` in `render.yaml` (auto-generates on first deploy).

---

### SEC-02 — Database Credentials

- [ ] `DB_PASSWORD` is a strong random password (min 20 chars)
- [ ] DB port 5432 is NOT exposed to the public internet in production (internal Render network only)
- [ ] `DB_USER` has only the required permissions (SELECT, INSERT, UPDATE, DELETE on app tables — no SUPERUSER)

**Create a least-privilege DB user**:
```sql
CREATE USER summarize_app WITH PASSWORD 'strong-password-here';
GRANT CONNECT ON DATABASE summarize_db TO summarize_app;
GRANT USAGE ON SCHEMA public TO summarize_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO summarize_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO summarize_app;
```

---

### SEC-03 — `.env` File Never Committed

- [ ] `.env` is listed in `.gitignore`
- [ ] `.env` does NOT appear in `git ls-files`
- [ ] `.env.example` is committed with placeholder values only

**Verify**:
```bash
git ls-files | grep "\.env$"
# Must return nothing
```

If `.env` was accidentally committed:
```bash
git rm --cached backend/.env
git commit -m "security: remove .env from tracking"
# Also rotate all secrets that were exposed
```

---

### SEC-04 — SQL Injection Prevention

All database queries use asyncpg parameterized queries:

```python
# CORRECT — parameterized
await conn.fetch("SELECT * FROM users WHERE email = $1", email)

# NEVER DO THIS — string interpolation
await conn.fetch(f"SELECT * FROM users WHERE email = '{email}'")  # VULNERABLE
```

- [ ] No f-string SQL anywhere in `app/db/repositories/`
- [ ] Grep verification: `grep -r "f\"SELECT\|f'SELECT" backend/app/db/`  → must return nothing

---

### SEC-05 — CORS Configuration

Development allows `localhost`:
```python
# Development .env
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

Production must specify exact origins:
```
CORS_ORIGINS=https://your-app.vercel.app,https://your-custom-domain.com
```

- [ ] `CORS_ORIGINS` does NOT contain `*` in production
- [ ] Options requests return the correct `Access-Control-Allow-Origin` header

---

### SEC-06 — File Upload Security

- [ ] MIME type validated server-side (not just file extension check)
- [ ] Max file size enforced before reading bytes (`MAX_UPLOAD_SIZE_MB=20`)
- [ ] Uploaded files never executed — only read for text extraction
- [ ] Temp files (if any) cleaned up after processing

```python
# In summarize.py route — validate before reading
ALLOWED_MIME = {"application/pdf"}
if file.content_type not in ALLOWED_MIME:
    raise HTTPException(status_code=400, detail="Only PDF files accepted")

contents = await file.read()
if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
    raise HTTPException(status_code=413, detail="File too large")
```

---

### SEC-07 — JWT Security

- [ ] Access token TTL: 30 minutes
- [ ] Refresh token TTL: 7 days
- [ ] Tokens include `type` claim (`access` vs `refresh`) to prevent refresh token reuse as access token
- [ ] Invalid tokens return 401 with no detail about why (don't leak info)
- [ ] Algorithm is `HS256` — do not allow `none` algorithm

```python
# In decode_token — always specify algorithms explicitly
jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
# NOT: jwt.decode(token, settings.SECRET_KEY)  ← allows none algorithm attack
```

---

## High Priority Security Items

### SEC-08 — Rate Limiting

```python
# app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# On routes:
@router.post("/summarize/text")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def summarize_text(request: Request, ...):
    ...
```

- [ ] Rate limiting applied to all `/api/v1/*` routes
- [ ] Extra-strict rate limiting on `/auth/login` (5/minute) to prevent brute force
- [ ] 429 responses include `Retry-After` header

---

### SEC-09 — Input Validation

- [ ] All Pydantic models have `min_length`, `max_length`, and type constraints
- [ ] No user-supplied data passed directly to AI prompts without sanitization
- [ ] No path traversal possible in file names (`original_filename` stored as metadata only — never used to open files)

```python
class TextSummarizeRequest(BaseModel):
    text: str = Field(min_length=50, max_length=100_000)
    summary_length: Literal["short", "medium", "long"] = "medium"
    format: Literal["paragraph", "bullets"] = "paragraph"
```

---

### SEC-10 — Error Response Sanitization

- [ ] Stack traces never returned in API responses
- [ ] Internal error messages not leaked to clients (use generic "Internal server error" messages)
- [ ] Only the custom error handler responses reach clients

```python
# app/core/exception_handlers.py
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)   # log full trace
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )
```

---

### SEC-11 — HTTPS / TLS

- [ ] Production runs behind Render's HTTPS (automatic — Render provides TLS certificates via Let's Encrypt)
- [ ] No HTTP endpoints in production (Render redirects HTTP → HTTPS by default)
- [ ] HSTS header set: `Strict-Transport-Security: max-age=31536000; includeSubDomains`

---

### SEC-12 — Logging Security

- [ ] Passwords are NEVER logged (mask in log output)
- [ ] API keys are NEVER logged
- [ ] JWT tokens are NEVER logged
- [ ] Request bodies for auth endpoints are NOT logged in full

```python
# Redact sensitive fields in structured logs
SENSITIVE_FIELDS = {"password", "hashed_password", "access_token", "refresh_token", "OPENAI_API_KEY"}
```

---

## Medium Priority Security Items

### SEC-13 — Dependency Auditing

```bash
# Check for known vulnerabilities in installed packages
pip install pip-audit
pip-audit

# Run in CI on every push
```

- [ ] `pip-audit` runs in CI (Phase 4)
- [ ] No HIGH or CRITICAL vulnerabilities in `requirements.txt`
- [ ] Dependencies pinned to specific versions (not `>=`) in `requirements.txt`

---

### SEC-14 — Docker Security

- [ ] App container runs as non-root user (`appuser`)
- [ ] Multi-stage build reduces attack surface (no build tools in runtime image)
- [ ] `COPY . .` happens after dependency install (Docker layer cache optimization + avoids leaking files)
- [ ] No secrets in Dockerfile or Docker image layers
- [ ] `.dockerignore` prevents `.env` from being copied into image

**`backend/.dockerignore`**:
```
.env
venv/
__pycache__/
*.pyc
.pytest_cache/
htmlcov/
uploads/
*.log
```

---

### SEC-15 — OpenAI API Key Scope

- [ ] `OPENAI_API_KEY` has usage limits set in OpenAI Dashboard (monthly spend cap)
- [ ] Key is scoped to the minimum required permissions
- [ ] Key is rotated if compromised (update Render env var + redeploy)

---

## Production Pre-Deploy Checklist

Run this before every production deploy:

```bash
# 1. Confirm no secrets in git history
git log --all --full-history -- "*.env" | head -5
# Should return nothing meaningful

# 2. Audit dependencies
pip-audit

# 3. Confirm DEBUG is false in render.yaml
grep "DEBUG" render.yaml
# Should show: value: "false"

# 4. Confirm CORS is not wildcard
grep "CORS_ORIGINS" render.yaml
# Should NOT contain *

# 5. Run full test suite
pytest --cov=app --cov-fail-under=80

# 6. Build Docker image locally
docker build -f docker/Dockerfile -t ai-summarize:prod .
docker run --rm ai-summarize:prod python -c "from app.main import create_app; create_app(); print('OK')"
```

---

## Security Incident Response

If a secret is compromised:

1. Immediately rotate the secret (generate new value)
2. Update the env var in Render Dashboard
3. Trigger a redeploy
4. Revoke the old key at the source (OpenAI Dashboard, HuggingFace Settings)
5. Check logs for unauthorized access during the exposure window
6. Document the incident and timeline

If `.env` was pushed to GitHub:
1. Immediately rotate ALL secrets in that file
2. Remove the file from git history:
   ```bash
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch backend/.env' HEAD
   git push origin --force --all
   ```
3. Contact GitHub support to purge caches
