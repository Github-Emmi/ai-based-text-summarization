# 09 — Testing Strategy

## Overview

The test suite uses `pytest` with `pytest-asyncio` for async test support and `httpx` for ASGI test client requests. Tests are split into **unit tests** (isolated service logic with mocked dependencies) and **integration tests** (full request cycle against a live test database). Coverage target is ≥ 80% across all source modules.

---

## Test Stack

| Tool | Version | Purpose |
|------|---------|---------|
| pytest | latest | Test runner and fixture engine |
| pytest-asyncio | latest | Async test function support |
| httpx | latest | ASGI test client for FastAPI |
| pytest-cov | latest | Coverage measurement |
| factory-boy | latest | Test data factories |
| freezegun | latest | Mock datetime in JWT tests |
| unittest.mock | stdlib | Mock AI clients, DB calls |

---

## Directory Structure

```
backend/tests/
├── conftest.py               ← shared fixtures: app, db, auth_headers, test_user
├── unit/
│   ├── test_summarizer.py    ← SummarizerService with mocked AI client
│   ├── test_pdf_extractor.py ← PDFExtractor with sample PDF bytes
│   ├── test_preprocessor.py  ← text cleaning + language detection
│   ├── test_keyword_extractor.py ← KeyBERT with mocked model
│   └── test_auth.py          ← password hashing, JWT encode/decode
└── integration/
    ├── test_health.py        ← GET /health, GET /health/db
    ├── test_auth_endpoints.py ← POST /auth/register, /login, /refresh
    ├── test_summarize_text.py ← POST /api/v1/summarize/text
    ├── test_summarize_pdf.py  ← POST /api/v1/summarize/pdf
    ├── test_chat.py           ← POST /api/v1/chat, GET /api/v1/chat/{id}
    └── test_history.py        ← GET /api/v1/history/summaries (pagination)
```

---

## `conftest.py`

```python
import pytest
import asyncio
import asyncpg
import httpx
from app.main import create_app
from app.core.config import settings
from app.core.security import hash_password, create_access_token

TEST_DB_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}_test"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_pool():
    pool = await asyncpg.create_pool(TEST_DB_URL, min_size=1, max_size=5)
    yield pool
    await pool.close()

@pytest.fixture
async def db(db_pool):
    async with db_pool.acquire() as conn:
        transaction = conn.transaction()
        await transaction.start()
        yield conn
        await transaction.rollback()   # rollback after each test = clean state

@pytest.fixture
async def client(db):
    app = create_app()
    # Override DB pool dependency to use test transaction
    app.dependency_overrides[get_db] = lambda: db
    async with httpx.AsyncClient(app=app, base_url="http://test") as c:
        yield c

@pytest.fixture
async def test_user(db):
    query = """
        INSERT INTO users (id, email, hashed_password, is_active)
        VALUES (gen_random_uuid(), $1, $2, true)
        RETURNING id, email
    """
    row = await db.fetchrow(query, "test@example.com", hash_password("Test1234!"))
    return dict(row)

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(str(test_user["id"]))
    return {"Authorization": f"Bearer {token}"}
```

---

## Unit Test Examples

### `tests/unit/test_summarizer.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.summarizer import SummarizerService

SAMPLE_TEXT = "A" * 500   # 500-char dummy text

@pytest.mark.asyncio
async def test_summarize_returns_summary():
    with patch("app.ai.router.route_summarize", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "text": "This is a concise summary.",
            "model": "gpt-4o-mini",
            "tokens_used": 100,
        }
        service = SummarizerService()
        result = await service.summarize(SAMPLE_TEXT, length="medium", format="paragraph")

    assert result["summary"] == "This is a concise summary."
    assert result["model_used"] == "gpt-4o-mini"
    assert result["tokens_used"] == 100


@pytest.mark.asyncio
async def test_summarize_falls_back_to_huggingface():
    import openai
    with patch("app.ai.openai_client.openai_complete", side_effect=openai.APIError("fail", request=None, body=None)):
        with patch("app.ai.huggingface_client.hf_api_complete", new_callable=AsyncMock) as mock_hf:
            mock_hf.return_value = {"text": "HF summary", "model": "bart-large-cnn", "tokens_used": None}
            service = SummarizerService()
            result = await service.summarize(SAMPLE_TEXT, length="short", format="paragraph")

    assert result["model_used"] == "bart-large-cnn"
```

### `tests/unit/test_pdf_extractor.py`

```python
import pytest
from app.services.pdf_extractor import PDFExtractor

def test_extract_text_from_valid_pdf():
    # Load a sample PDF fixture from tests/fixtures/sample.pdf
    with open("tests/fixtures/sample.pdf", "rb") as f:
        pdf_bytes = f.read()
    extractor = PDFExtractor()
    text = extractor.extract(pdf_bytes)
    assert len(text) > 50
    assert isinstance(text, str)

def test_extract_raises_on_empty_pdf():
    from app.core.exceptions import PDFExtractionError
    extractor = PDFExtractor()
    with pytest.raises(PDFExtractionError):
        extractor.extract(b"not a pdf")
```

### `tests/unit/test_auth.py`

```python
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from freezegun import freeze_time
from datetime import datetime, timezone

def test_password_hash_and_verify():
    hashed = hash_password("TestPass123!")
    assert verify_password("TestPass123!", hashed)
    assert not verify_password("WrongPass", hashed)

def test_access_token_contains_user_id():
    token = create_access_token("user-uuid-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-uuid-123"
    assert payload["type"] == "access"

@freeze_time("2026-04-29 12:00:00")
def test_expired_token_raises():
    import time
    from app.core.config import settings
    # Create a token that expired 1 second ago
    from datetime import timedelta
    from jose import jwt
    expired_payload = {
        "sub": "user-uuid-123",
        "type": "access",
        "exp": datetime(2026, 4, 29, 11, 59, 59, tzinfo=timezone.utc),
    }
    token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(ValueError):
        decode_token(token)
```

---

## Integration Test Examples

### `tests/integration/test_health.py`

```python
import pytest

@pytest.mark.asyncio
async def test_health_returns_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data

@pytest.mark.asyncio
async def test_health_db_connected(client):
    resp = await client.get("/health/db")
    assert resp.status_code == 200
    assert resp.json()["database"] == "connected"
```

### `tests/integration/test_auth_endpoints.py`

```python
import pytest

@pytest.mark.asyncio
async def test_register_creates_user(client):
    resp = await client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "StrongPass1!"
    })
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@example.com"

@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client, test_user):
    resp = await client.post("/auth/register", json={
        "email": "test@example.com",   # already exists from test_user fixture
        "password": "AnotherPass1!"
    })
    assert resp.status_code == 409

@pytest.mark.asyncio
async def test_login_returns_tokens(client, test_user):
    resp = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "Test1234!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
```

### `tests/integration/test_summarize_text.py`

```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_summarize_text_success(client, auth_headers):
    mock_response = {"text": "Summary text here.", "model": "gpt-4o-mini", "tokens_used": 50}
    with patch("app.ai.router.route_summarize", new_callable=AsyncMock, return_value=mock_response):
        resp = await client.post(
            "/api/v1/summarize/text",
            json={"text": "A" * 100, "summary_length": "short", "format": "paragraph"},
            headers=auth_headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"] == "Summary text here."
    assert data["model_used"] == "gpt-4o-mini"

@pytest.mark.asyncio
async def test_summarize_text_requires_auth(client):
    resp = await client.post("/api/v1/summarize/text", json={"text": "A" * 100})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_summarize_text_too_short(client, auth_headers):
    resp = await client.post(
        "/api/v1/summarize/text",
        json={"text": "Too short"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
```

---

## Test Commands

```bash
# Navigate to backend and activate venv
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage report (terminal)
pytest --cov=app --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run a specific test file
pytest tests/unit/test_summarizer.py -v

# Run a specific test
pytest tests/unit/test_auth.py::test_password_hash_and_verify -v

# Run with verbose output + show stdout
pytest -v -s

# Stop on first failure
pytest -x

# Run tests matching a keyword
pytest -k "summarize" -v
```

---

## `pytest.ini`

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*
log_cli = true
log_cli_level = INFO
```

---

## Coverage Targets

| Module | Target Coverage |
|--------|----------------|
| `app/core/` | ≥ 90% |
| `app/services/` | ≥ 85% |
| `app/ai/` | ≥ 80% |
| `app/api/v1/` | ≥ 85% |
| `app/db/repositories/` | ≥ 80% |
| **Overall** | **≥ 80%** |

---

## Test Fixtures Required

Create `tests/fixtures/` with:

```
tests/fixtures/
├── sample.pdf              ← a small valid PDF for PDF extraction tests
└── sample_long.pdf         ← a multi-page PDF for edge case tests
```

Generate a minimal test PDF:
```bash
python -c "
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
doc = SimpleDocTemplate('tests/fixtures/sample.pdf')
styles = getSampleStyleSheet()
doc.build([Paragraph('This is a test document for unit testing the PDF extractor.', styles['Normal'])])
print('sample.pdf created')
"
```

---

## CI Integration (Phase 4)

The GitHub Actions workflow (`.github/workflows/ci.yml`) will run:

```yaml
- name: Run Tests
  run: |
    cd backend
    source venv/bin/activate
    pytest --cov=app --cov-fail-under=80 -v
```

Builds fail if coverage drops below 80%.
