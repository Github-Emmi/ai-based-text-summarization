# 04 — Project Structure

## Overview

The repository uses a monorepo layout with clear separation between documentation, CI configuration, the backend application, and future frontend. Every folder has a defined purpose — no catch-all directories.

---

## Full Directory Tree

```
ai-based-text-summarization/               ← repo root
│
├── .github/
│   ├── agents/
│   │   └── AI-BASED-TEXT-SUMMARIZATION.agent.md   ← specialist agent
│   └── workflows/                                  ← CI/CD (Phase 4)
│       └── ci.yml
│
├── docs/                                           ← all architecture docs
│   ├── 00-project-overview.md
│   ├── 01-github-setup.md
│   ├── 02-environment-setup.md
│   ├── 03-architecture.md
│   ├── 04-project-structure.md             ← this file
│   ├── 05-database-schema.md
│   ├── 06-api-design.md
│   ├── 07-ai-integration.md
│   ├── 08-advanced-features.md
│   ├── 09-testing-strategy.md
│   ├── 10-deployment-render.md
│   └── 11-security-checklist.md
│
├── backend/                                        ← all backend code
│   │
│   ├── app/                                        ← FastAPI application package
│   │   │
│   │   ├── main.py                                 ← app factory + lifespan + router registration
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py                         ← /auth/register, /auth/login, /auth/refresh
│   │   │       ├── summarize.py                    ← /api/v1/summarize/text, /pdf
│   │   │       ├── chat.py                         ← /api/v1/chat
│   │   │       ├── history.py                      ← /api/v1/history
│   │   │       └── export.py                       ← /api/v1/export/{summary_id}
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                           ← pydantic-settings Settings class
│   │   │   ├── dependencies.py                     ← get_db(), get_current_user() FastAPI deps
│   │   │   ├── exceptions.py                       ← custom exception classes
│   │   │   ├── exception_handlers.py               ← register handlers on the app
│   │   │   ├── logging.py                          ← structured JSON logger setup
│   │   │   └── security.py                         ← JWT encode/decode, bcrypt helpers
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py                          ← asyncpg pool creation + shutdown
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py                         ← SQLAlchemy declarative base + UUID helper
│   │   │   │   ├── user.py                         ← users table
│   │   │   │   ├── summary.py                      ← summaries table
│   │   │   │   ├── chat_session.py                 ← chat_sessions table
│   │   │   │   └── chat_message.py                 ← chat_messages table
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       ├── base.py                         ← generic CRUD helpers
│   │   │       ├── user_repository.py
│   │   │       ├── summary_repository.py
│   │   │       ├── chat_session_repository.py
│   │   │       └── chat_message_repository.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                             ← RegisterRequest, LoginRequest, TokenResponse
│   │   │   ├── summarize.py                        ← TextSummarizeRequest, PDFSummarizeRequest, SummaryResponse
│   │   │   ├── chat.py                             ← ChatRequest, ChatResponse, MessageSchema
│   │   │   ├── history.py                          ← PaginatedSummaryResponse, PaginatedChatResponse
│   │   │   └── common.py                           ← ErrorResponse, HealthResponse, PaginationMeta
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── summarizer.py                       ← orchestrates AI routing + keyword extraction
│   │   │   ├── pdf_extractor.py                    ← pdfplumber text extraction
│   │   │   ├── preprocessor.py                     ← text cleaning + language detection
│   │   │   ├── chat.py                             ← context window management + AI call
│   │   │   ├── keyword_extractor.py                ← KeyBERT extraction
│   │   │   ├── export.py                           ← reportlab PDF generation
│   │   │   └── auth.py                             ← password hashing + JWT operations
│   │   │
│   │   └── ai/
│   │       ├── __init__.py
│   │       ├── router.py                           ← primary/fallback selection logic
│   │       ├── openai_client.py                    ← async OpenAI call with retry + timeout
│   │       ├── huggingface_client.py               ← HF Inference API or local pipeline
│   │       └── prompts.py                          ← all system/user prompt templates
│   │
│   ├── alembic/
│   │   ├── env.py                                  ← Alembic env config (uses app Settings)
│   │   ├── script.py.mako                          ← migration file template
│   │   └── versions/
│   │       ├── 0001_create_users.py
│   │       ├── 0002_create_summaries.py
│   │       ├── 0003_create_chat_sessions.py
│   │       └── 0004_create_chat_messages.py
│   │
│   ├── docker/
│   │   ├── Dockerfile                              ← multi-stage build (builder + runtime)
│   │   └── entrypoint.sh                           ← run alembic upgrade then uvicorn
│   │
│   ├── tests/
│   │   ├── conftest.py                             ← pytest fixtures (app, db, auth headers)
│   │   ├── unit/
│   │   │   ├── test_summarizer.py
│   │   │   ├── test_pdf_extractor.py
│   │   │   ├── test_preprocessor.py
│   │   │   ├── test_keyword_extractor.py
│   │   │   └── test_auth.py
│   │   └── integration/
│   │       ├── test_health.py
│   │       ├── test_auth_endpoints.py
│   │       ├── test_summarize_text.py
│   │       ├── test_summarize_pdf.py
│   │       ├── test_chat.py
│   │       └── test_history.py
│   │
│   ├── uploads/                                    ← temp PDF storage (gitignored)
│   │
│   ├── main.py                                     ← dev runner: uvicorn with reload
│   ├── alembic.ini                                 ← Alembic config (points to alembic/ dir)
│   ├── requirements.txt                            ← pinned production dependencies
│   ├── requirements-dev.txt                        ← pytest, httpx, black, ruff extras
│   ├── .env.example                                ← all env vars documented (no real values)
│   ├── .env                                        ← real values (gitignored)
│   ├── docker-compose.yml                          ← app + db + adminer services
│   └── pytest.ini                                  ← pytest configuration
│
├── .gitignore
├── README.md
└── LICENSE                                         ← MIT
```

---

## Key File Purposes

### `backend/app/main.py`

```python
# Responsibilities:
# 1. Create FastAPI application with title, version, description
# 2. Register lifespan (startup: open DB pool; shutdown: close pool)
# 3. Add CORSMiddleware with settings.CORS_ORIGINS
# 4. Register exception handlers (validation, HTTP, unhandled)
# 5. Include routers: auth, summarize, chat, history, export
# 6. Mount /health endpoint (no auth required)
```

### `backend/app/core/config.py`

```python
# Uses pydantic-settings BaseSettings
# Reads from .env file automatically
# All settings are typed and validated at startup
# Provides a single settings singleton imported across the app
```

### `backend/app/db/session.py`

```python
# Creates an asyncpg connection pool on app startup
# Exposes get_pool() for dependency injection
# Closes the pool on app shutdown
# Pool config: min_size=2, max_size=10 (configurable via env)
```

### `backend/app/db/repositories/`

```python
# All database I/O lives here — NEVER in services or routes
# Repositories take a pool connection as a parameter
# No ORM sessions — raw asyncpg for performance
# Return typed dataclass/Pydantic objects, never raw DB rows
```

### `backend/app/ai/router.py`

```python
# Single entry point for AI calls
# Checks if OpenAI client is configured
# Attempts OpenAI call, catches openai.APIError
# Falls back to HuggingFace on failure
# Logs which model was used and token count
```

### `backend/app/ai/prompts.py`

```python
# Centralized prompt management — no prompt strings scattered in services
# SUMMARIZE_SYSTEM_PROMPT: role + format instructions
# CHAT_SYSTEM_PROMPT: document context window injection
# Parameterized: accepts length, format, language
```

---

## Dependency Flow

```
Route Handler
    │ depends on
    ▼
Dependency (get_db, get_current_user)
    │ injects
    ▼
Service Layer
    │ calls
    ├──► Repository (DB reads/writes)
    └──► AI Client (OpenAI / HuggingFace)
```

**Rule**: Routes never import repositories directly. Services never import routes. AI clients never import services.

---

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Files | `snake_case.py` | `pdf_extractor.py` |
| Classes | `PascalCase` | `SummarizerService` |
| Functions | `snake_case` | `extract_text()` |
| DB columns | `snake_case` | `created_at`, `user_id` |
| Env vars | `UPPER_SNAKE_CASE` | `OPENAI_API_KEY` |
| API routes | `kebab-case` | `/api/v1/summarize/text` |
| Pydantic models | `PascalCase` | `TextSummarizeRequest` |
| Alembic files | `NNNN_description.py` | `0001_create_users.py` |

---

## Module Import Rules

- `app.core.config` — imported by all other modules that need settings
- `app.db.session` — imported only by `app.core.dependencies`
- `app.db.repositories.*` — imported only by `app.services.*`
- `app.ai.*` — imported only by `app.services.summarizer` and `app.services.chat`
- `app.services.*` — imported only by `app.api.v1.*`
- `app.schemas.*` — imported by routes and services (shared Pydantic models)

This enforces a strict one-directional dependency graph and prevents circular imports.
