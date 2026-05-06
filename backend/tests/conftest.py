"""
Pytest fixtures for the AI-Based Text Summarization backend.

Fixture tiers:
  1. `client` (session scope) — httpx AsyncClient with NO DB dependency.
     Used by: test_health.py. Pool never created (lifespan not triggered by ASGITransport).

  2. DB fixtures (function scope) — require a running PostgreSQL.
     `db`:      function-scoped direct asyncpg Connection (rolls back after each test).
     `auth_client`: function-scoped AsyncClient with get_db overridden to use `db`.
     `test_user`, `auth_headers`: helpers that depend on `db`.

     Note: each fixture opens its own asyncpg.connect() in the test's event loop
     (no session-scoped pool) to avoid "Future attached to different loop" errors
     on Python 3.11+ with pytest-asyncio >= 0.21.

  Usage:
    - Health tests: use `client`
    - Auth integration tests: use `auth_client`, `test_user`, `auth_headers`
"""

import socket

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.main import create_app

# ── Tier 1: plain httpx client (no DB) ────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear slowapi in-memory rate limit counters before each test.

    Without this, repeated login calls in successive tests exhaust the
    5/minute limit on /auth/login, causing spurious 429 failures.
    """
    from app.core.limiter import limiter
    limiter._storage.reset()
    yield


@pytest_asyncio.fixture
async def client():
    """
    Session-scoped AsyncClient backed by the FastAPI ASGI app.
    ASGITransport does not trigger lifespan, so no DB pool is created here.
    The /health endpoint works without a pool; /health/db returns 503.
    """
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ── Tier 2: DB-backed fixtures ─────────────────────────────────────────────────

def _db_is_available() -> bool:
    """Synchronous TCP probe: returns True if PostgreSQL port is accepting connections."""
    try:
        with socket.create_connection((settings.DB_HOST, settings.DB_PORT), timeout=2):
            return True
    except OSError:
        return False


@pytest_asyncio.fixture
async def db():
    """
    Function-scoped transactional asyncpg connection.

    Opens a direct asyncpg.connect() in the current test's event loop — no
    session-scoped pool — to avoid cross-loop Future errors on Python 3.14 with
    pytest-asyncio >= 0.21.  Every test gets a fresh connection; changes are
    rolled back after the test so each test starts from a clean state.
    """
    if not _db_is_available():
        pytest.skip(
            "Database not available — run 'docker-compose up -d' first, "
            "then re-run integration tests."
        )
    conn = await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        timeout=10,
    )
    transaction = conn.transaction()
    await transaction.start()
    try:
        yield conn
    finally:
        await transaction.rollback()
        await conn.close()


@pytest_asyncio.fixture
async def auth_client(db: asyncpg.Connection):
    """
    Function-scoped AsyncClient that overrides get_db with the test transaction.

    This means:
      - The app never tries to create its own pool (lifespan not triggered).
      - Every route handler and get_current_user see the same transactional
        connection, so inserts are visible within the test and rolled back after.
    """
    from app.core.dependencies import get_db as _get_db

    app = create_app()

    async def _override_db():
        yield db

    app.dependency_overrides[_get_db] = _override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db: asyncpg.Connection) -> dict:
    """
    Insert a test user directly into the DB via the transactional connection.
    Rolled back after the test — no cleanup SQL required.
    """
    row = await db.fetchrow(
        "INSERT INTO users (email, hashed_password, is_active) "
        "VALUES ($1, $2, true) "
        "RETURNING id, email, created_at",
        "test@example.com",
        hash_password("Test1234!"),
    )
    return dict(row)


@pytest.fixture
def auth_headers(test_user: dict) -> dict:
    """JWT Bearer headers for the test user."""
    token = create_access_token(str(test_user["id"]))
    return {"Authorization": f"Bearer {token}"}

