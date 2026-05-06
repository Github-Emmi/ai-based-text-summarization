# 03 — System Architecture

## Overview

The AI-Based Text Summarization Platform follows a **three-tier async architecture**: a stateless FastAPI application layer, a PostgreSQL persistence layer managed via asyncpg, and an external AI services layer (OpenAI + HuggingFace). All tiers are containerized for environment parity from local development to production on Render.

---

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
│   Next.js Frontend (future)  │  Swagger UI  │  External API Clients │
└─────────────────┬───────────────────────────────────────────────────┘
                  │ HTTPS  (port 443 in prod / 8000 in dev)
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FASTAPI APPLICATION LAYER                     │
│                                                                     │
│  ┌──────────────┐   ┌───────────────┐   ┌─────────────────────┐    │
│  │   Auth       │   │  Summarize    │   │  Chat / History     │    │
│  │  Router      │   │  Router       │   │  Router             │    │
│  │ /auth/*      │   │ /api/v1/      │   │ /api/v1/chat/*      │    │
│  │              │   │ summarize/*   │   │ /api/v1/history/*   │    │
│  └──────┬───────┘   └──────┬────────┘   └──────────┬──────────┘    │
│         │                  │                        │               │
│  ┌──────▼──────────────────▼────────────────────────▼──────────┐   │
│  │                    Service Layer                             │   │
│  │  AuthService  │  SummarizerService  │  ChatService          │   │
│  │               │  PDFExtractor       │  KeywordExtractor     │   │
│  │               │  TextPreprocessor   │  ExportService        │   │
│  └──────┬────────────────────┬──────────────────────┬──────────┘   │
│         │                    │                       │              │
│  ┌──────▼──────────┐  ┌──────▼──────────┐           │              │
│  │  DB Repository  │  │  AI Client      │           │              │
│  │  (asyncpg pool) │  │  Layer          │           │              │
│  └──────┬──────────┘  └──────┬──────────┘           │              │
└─────────┼────────────────────┼─────────────────────-┼──────────────┘
          │                    │                       │
          ▼                    ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
│  PostgreSQL 15  │  │  OpenAI API     │  │  HuggingFace API     │
│  (port 5432)    │  │  GPT-4o-mini    │  │  (BART fallback)     │
│  Adminer :8080  │  │  (primary)      │  │  or Local Model      │
└─────────────────┘  └─────────────────┘  └──────────────────────┘
```

---

## Component Responsibilities

### FastAPI Application Layer

| Component | File Path | Responsibility |
|-----------|-----------|----------------|
| App Factory | `app/main.py` | Create FastAPI instance, register routers, lifespan hooks |
| Config | `app/core/config.py` | Typed settings from `.env` via pydantic-settings |
| Lifespan | `app/main.py` | DB pool startup/shutdown, model warm-up |
| CORS Middleware | `app/main.py` | Restrict allowed origins |
| Exception Handlers | `app/core/exceptions.py` | Structured JSON error responses |
| Auth Router | `app/api/v1/auth.py` | Register, login, refresh token |
| Summarize Router | `app/api/v1/summarize.py` | Text + PDF summarization endpoints |
| Chat Router | `app/api/v1/chat.py` | Chat-with-document, history retrieval |
| History Router | `app/api/v1/history.py` | Paginated summary and chat history |
| Export Router | `app/api/v1/export.py` | PDF export of summaries |
| Dependencies | `app/core/dependencies.py` | `get_db()`, `get_current_user()` injection |

### Service Layer

| Service | File Path | Responsibility |
|---------|-----------|----------------|
| SummarizerService | `app/services/summarizer.py` | Route to OpenAI or HuggingFace, format output |
| PDFExtractor | `app/services/pdf_extractor.py` | Extract and clean text from PDF bytes |
| TextPreprocessor | `app/services/preprocessor.py` | Normalize whitespace, detect language |
| ChatService | `app/services/chat.py` | Build context window, call OpenAI, persist messages |
| KeywordExtractor | `app/services/keyword_extractor.py` | KeyBERT semantic keyword ranking |
| ExportService | `app/services/export.py` | Generate PDF bytes with reportlab |
| AuthService | `app/services/auth.py` | Hash passwords, issue/verify JWT tokens |

### Data Layer

| Component | File Path | Responsibility |
|-----------|-----------|----------------|
| DB Session | `app/db/session.py` | asyncpg pool creation, connection lifecycle |
| Models | `app/db/models/` | SQLAlchemy table definitions |
| Repositories | `app/db/repositories/` | All SQL queries — no raw SQL in services |
| Alembic | `alembic/` | Schema migration history |

### AI Client Layer

| Client | File Path | Responsibility |
|--------|-----------|----------------|
| OpenAI Client | `app/ai/openai_client.py` | Async OpenAI call with retry + timeout |
| HuggingFace Client | `app/ai/huggingface_client.py` | HF Inference API or local pipeline |
| AI Router | `app/ai/router.py` | Select primary vs. fallback, handle errors |

---

## Request Flow — Text Summarization

```
POST /api/v1/summarize/text
  │
  ├─ 1. JWT Bearer token validated (Dependency: get_current_user)
  ├─ 2. Pydantic model validates request body (min/max length, format param)
  ├─ 3. TextPreprocessor.clean() normalizes input
  ├─ 4. Language detected (langdetect)
  ├─ 5. SummarizerService.summarize()
  │      ├─ Try: OpenAI GPT-4o-mini
  │      │       └─ Structured prompt with length + format instructions
  │      └─ Except OpenAI error: HuggingFace BART fallback
  ├─ 6. KeywordExtractor.extract() runs on original text
  ├─ 7. SummaryRepository.create() persists to PostgreSQL
  └─ 8. Return SummaryResponse JSON
```

## Request Flow — PDF Summarization

```
POST /api/v1/summarize/pdf
  │
  ├─ 1. JWT Bearer token validated
  ├─ 2. File validated: MIME type = application/pdf, size ≤ 20MB
  ├─ 3. PDFExtractor.extract(file_bytes) → raw_text
  ├─ 4. TextPreprocessor.clean(raw_text) → clean_text
  ├─ 5. Language detected
  ├─ 6. [same as text flow from step 5 above]
  └─ 7. Return SummaryResponse JSON
```

---

## Database Architecture

```
PostgreSQL 15 Database: summarize_db
│
├── users
│   └── id, email, hashed_password, is_active, created_at, updated_at
│
├── summaries
│   └── id, user_id (FK), input_hash, original_text, summary, format,
│       word_count, language, model_used, keywords (JSON), created_at
│
├── chat_sessions
│   └── id, user_id (FK), summary_id (FK), title, created_at, updated_at
│
└── chat_messages
    └── id, session_id (FK), role (user|assistant), content, created_at
```

---

## AI Integration Architecture

```
SummarizerService.summarize(text, length, format)
  │
  ├─ ai_router.route(text)
  │     │
  │     ├─ [Primary] OpenAIClient.complete(prompt)
  │     │     ├─ model: gpt-4o-mini
  │     │     ├─ system prompt: role + format instructions
  │     │     ├─ temperature: 0.3 (deterministic)
  │     │     ├─ max_tokens: configurable per length setting
  │     │     ├─ retry: 3x with exponential backoff
  │     │     └─ timeout: 30s
  │     │
  │     └─ [Fallback] HuggingFaceClient.complete(text)
  │           ├─ model: facebook/bart-large-cnn
  │           ├─ source: HuggingFace Inference API (dev)
  │           │          or local pipeline (prod if USE_LOCAL_MODEL=true)
  │           └─ truncate to model max_length (1024 tokens)
  │
  └─ Return: { summary_text, model_used, tokens_used }
```

---

## Infrastructure Architecture

### Local Development (Docker Compose)

```
docker-compose.yml
  │
  ├── service: app
  │     image: backend/docker/Dockerfile (multi-stage)
  │     ports: 8000:8000
  │     volumes: ./:/app (bind mount for hot-reload)
  │     depends_on: db
  │     environment: from .env
  │
  ├── service: db
  │     image: postgres:15-alpine
  │     ports: 5432:5432
  │     volumes: postgres_data (named volume, persists across restarts)
  │     healthcheck: pg_isready
  │
  └── service: adminer
        image: adminer:latest
        ports: 8080:8080
        depends_on: db
```

### Production (Render)

```
Render Platform
  │
  ├── Web Service: ai-text-summarization-api
  │     runtime: Docker
  │     region: Oregon (US West)
  │     plan: Starter ($7/mo)
  │     env vars: set in Render dashboard
  │     health check: /health
  │     auto-deploy: on push to main
  │
  └── PostgreSQL: ai-text-summarization-db
        plan: Starter ($7/mo)
        version: 15
        connection: internal URL injected as DATABASE_URL
```

---

## Security Architecture

```
Request → TLS (Render) → CORS check → Rate Limiter (slowapi)
        → Auth middleware → JWT validation → Route handler
        → Input validation (Pydantic) → Service → DB
```

- All secrets in environment variables (never in code)
- Bcrypt for password hashing (cost factor 12)
- HS256 JWT with 30-min access token + 7-day refresh token
- Parameterized queries only (no raw string SQL)
- File upload: MIME-type check + max-size enforcement before reading bytes
- CORS origins locked to specific domains in production
- Rate limiting: 30 requests/minute per IP

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Async framework | FastAPI + asyncpg | Non-blocking I/O for AI calls (latency ~3–8s) |
| DB driver | asyncpg (not SQLAlchemy async) | ~3x faster than SQLAlchemy async for PostgreSQL |
| Primary AI | OpenAI GPT-4o-mini | Best quality/cost ratio; structured output support |
| AI fallback | HuggingFace BART | Open-source, no API key required, deployable locally |
| PDF extraction | pdfplumber | Better text layout handling than pypdf for formatted docs |
| Auth | JWT (stateless) | Scales horizontally without shared session store |
| Migration | Alembic | Industry standard for SQLAlchemy schema versioning |
| Config | pydantic-settings v2 | Type-safe env var parsing with validation at startup |
