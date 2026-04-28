# 00 — Project Overview

## Project Title
**AI-Based Text Summarization Platform**

## Mission Statement

Build a production-ready, enterprise-grade web API that accepts raw text or PDF documents, processes the content through state-of-the-art NLP models, and returns concise, structured summaries. The backend is the authoritative system of record for all summarization requests, user sessions, and chat history.

---

## System Workflow

```
User Input (Text / PDF)
        │
        ▼
  FastAPI Backend
  ┌───────────────────────────────┐
  │  Input Validation             │
  │  PDF Text Extraction          │
  │  Text Preprocessing           │
  │  AI Summarization Service ────┼──► OpenAI GPT-4o-mini (primary)
  │                               │    HuggingFace BART (fallback)
  │  Keyword Extraction           │
  │  Chat History Persistence     │
  │  PostgreSQL Storage           │
  └───────────────────────────────┘
        │
        ▼
  Structured JSON Response
  (summary, keywords, metadata)
```

---

## Objectives

| # | Objective | Priority |
|---|-----------|----------|
| 1 | Accept and validate text input and PDF file uploads | Must-Have |
| 2 | Extract and preprocess text from PDFs | Must-Have |
| 3 | Generate summaries via OpenAI GPT-4o-mini | Must-Have |
| 4 | HuggingFace BART fallback when OpenAI is unavailable | Must-Have |
| 5 | Persist all summaries and metadata to PostgreSQL | Must-Have |
| 6 | JWT-based user authentication and authorization | Must-Have |
| 7 | Chat-with-document with conversation history | High |
| 8 | Keyword extraction per document | High |
| 9 | Export summary as downloadable PDF | High |
| 10 | Multi-language summarization support | Medium |
| 11 | Rate limiting and abuse prevention | Must-Have (prod) |
| 12 | Full async operation throughout | Must-Have |

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Web Framework | FastAPI | 0.104+ | Async HTTP server, OpenAPI docs |
| Language | Python | 3.10+ | Type-safe backend |
| Database | PostgreSQL | 15 | Primary persistent store |
| Async DB Driver | asyncpg | latest | Non-blocking DB I/O |
| Schema Migrations | Alembic | latest | Version-controlled DB schema |
| AI Primary | OpenAI API | GPT-4o-mini | Summarization, chat-with-doc |
| AI Fallback | HuggingFace Transformers | facebook/bart-large-cnn | Offline summarization |
| PDF Extraction | pdfplumber | latest | Accurate text layout extraction |
| Auth | python-jose + passlib | latest | JWT tokens + bcrypt hashing |
| Keyword Extraction | KeyBERT | latest | Semantic keyword ranking |
| PDF Export | reportlab | latest | Generate downloadable summaries |
| Config Management | pydantic-settings v2 | latest | Typed env vars from `.env` |
| Rate Limiting | slowapi | latest | Per-IP request throttling |
| Testing | pytest + pytest-asyncio + httpx | latest | Unit and integration tests |
| Containerization | Docker + Docker Compose | latest | Dev and prod environment parity |
| Deploy Platform | Render | — | Web service + managed PostgreSQL |

---

## Functional Requirements

### FR-01: Input Handling
- Accept raw text string (min 50 chars, max 100,000 chars)
- Accept PDF file upload (max 20MB, PDF MIME type only)
- Reject invalid input with structured error responses

### FR-02: Text Processing
- Extract raw text from PDFs using pdfplumber
- Strip excessive whitespace, control characters, and page headers/footers
- Detect text language (langdetect) for multi-language routing

### FR-03: Summarization
- Call OpenAI GPT-4o-mini with structured system prompt
- Accept optional `summary_length` param: `short` | `medium` | `long`
- Accept optional `format` param: `paragraph` | `bullets`
- Fall back to HuggingFace BART if OpenAI returns error or is unavailable
- Persist result to `summaries` table with input hash (deduplication)

### FR-04: Output
- Return JSON: `{ summary, format, word_count, keywords, language, model_used, created_at }`
- Pagination on summary history endpoints
- Downloadable PDF endpoint for any saved summary

### FR-05: Authentication
- `POST /auth/register` — create user with hashed password
- `POST /auth/login` — return access + refresh JWT tokens
- `POST /auth/refresh` — rotate tokens
- All `/api/v1/*` routes require valid Bearer token

### FR-06: Chat History
- `POST /api/v1/chat` — send message in context of a summary document
- `GET /api/v1/chat/{session_id}` — retrieve full conversation
- Messages stored in `chat_messages` table with ordering preserved

---

## Evaluation Criteria

| Criterion | Weight | Target |
|-----------|--------|--------|
| Functionality | 80% | All endpoints pass integration tests |
| UI/UX Design | 85% | N/A (backend-only scope this phase) |
| Code Quality | 95% | Lint clean, typed, modular, no dead code |
| AI Integration | 85% | OpenAI + fallback working end-to-end |
| Innovation | 90% | Chat-with-doc, keyword extraction, multi-lang |
| Documentation | 80% | All 11 docs complete, README accurate |

---

## Deliverables

| # | Deliverable | Status |
|---|------------|--------|
| 1 | Source code pushed to GitHub repository | Phase 0 |
| 2 | Architecture documentation (this `docs/` folder) | Phase 0 |
| 3 | `README.md` with full setup instructions | Phase 0 |
| 4 | Working FastAPI backend with Docker | Phase 1 |
| 5 | Core summarization API (text + PDF) | Phase 2 |
| 6 | Advanced features (auth, chat, keywords, export) | Phase 3 |
| 7 | Production-hardened deploy on Render | Phase 4 |

---

## Non-Functional Requirements

- **Performance**: Summarization response < 10s (p95) for documents ≤ 5,000 words
- **Availability**: 99.5% uptime on Render Starter tier
- **Security**: OWASP Top 10 compliance (see `docs/11-security-checklist.md`)
- **Scalability**: Stateless FastAPI instances — horizontally scalable behind load balancer
- **Observability**: Structured JSON logging with request IDs on all routes

---

## Phase Summary

| Phase | Name | Key Deliverable | Gate |
|-------|------|-----------------|------|
| 0 | Repo & Env Bootstrap | GitHub repo, venv, .gitignore | Explicit approval |
| 1 | Foundation | Docker + FastAPI + PostgreSQL pool + /health | Explicit approval |
| 2 | Core Summarization | Text + PDF endpoints + AI service | Explicit approval |
| 3 | Advanced Features | Auth + chat + keywords + PDF export | Explicit approval |
| 4 | Production Hardening | Tests + rate limiting + Render deploy | Explicit approval |

---

## Related Documentation

| Doc | File |
|-----|------|
| GitHub Setup | [01-github-setup.md](./01-github-setup.md) |
| Environment Setup | [02-environment-setup.md](./02-environment-setup.md) |
| Architecture | [03-architecture.md](./03-architecture.md) |
| Project Structure | [04-project-structure.md](./04-project-structure.md) |
| Database Schema | [05-database-schema.md](./05-database-schema.md) |
| API Design | [06-api-design.md](./06-api-design.md) |
| AI Integration | [07-ai-integration.md](./07-ai-integration.md) |
| Advanced Features | [08-advanced-features.md](./08-advanced-features.md) |
| Testing Strategy | [09-testing-strategy.md](./09-testing-strategy.md) |
| Render Deployment | [10-deployment-render.md](./10-deployment-render.md) |
| Security Checklist | [11-security-checklist.md](./11-security-checklist.md) |
