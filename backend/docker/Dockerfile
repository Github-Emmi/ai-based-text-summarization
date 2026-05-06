# ── Stage 1: Builder ──────────────────────────────────────────────────────────
# Install all Python dependencies into /install so the runtime stage
# can copy them without needing build tools (gcc, etc.).
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies needed for asyncpg (C extension), bcrypt, etc.
# asyncpg implements the Postgres wire protocol directly — libpq-dev is not needed.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Upgrade pip first to avoid known CVEs (CVE-2026-1703, CVE-2026-3219)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime system dependencies only (no build tools)
# asyncpg does not need libpq5 — it uses its own protocol implementation.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    # Create a non-root user for security (SEC-12)
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY . .

# Create uploads directory owned by the app user
RUN mkdir -p uploads && chown appuser:appgroup uploads

# Switch to non-root user — never run as root in production
USER appuser

EXPOSE 8000

# entrypoint.sh runs: alembic upgrade head → uvicorn
ENTRYPOINT ["./docker/entrypoint.sh"]
