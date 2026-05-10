# AI-Based Text Summarization Platform

A production-ready, full-stack AI platform for text and PDF summarization — built with FastAPI, Next.js, PostgreSQL, and a dual-provider AI layer using OpenRouter (Llama 3.3 70B) and HuggingFace BART.

## Author

**Aghason Emmanuel Ibeabuchi**  
GitHub: [github.com/Github-Emmi](https://github.com/Github-Emmi/)

## Links

| | URL |
|---|---|
| **GitHub Repository** | https://github.com/Github-Emmi/ai-based-text-summarization/tree/main |
| **Frontend (Vercel)** | https://ai-based-text-summarization.vercel.app |
| **Backend API (Render)** | https://ai-based-text-summarization-u4qa.onrender.com |
| **Swagger UI** | https://ai-based-text-summarization-u4qa.onrender.com/docs |
| **ReDoc** | https://ai-based-text-summarization-u4qa.onrender.com/redoc |


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

## API — Verified Endpoints

All endpoints below were curl-tested against the live production backend.

```bash
BASE=https://ai-based-text-summarization-u4qa.onrender.com

# Health check — no auth required
curl $BASE/health
# → {"status":"ok","environment":"production","version":"1.0.0"}

# Database health — no auth required
curl $BASE/health/db
# → {"status":"ok","database":"connected","pool_size":2,"pool_free":2}

# Register a new user
curl -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"YourPass1!"}'
# → HTTP 201 — user created

# Login and receive tokens
curl -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"YourPass1!"}'
# → {"access_token":"...","refresh_token":"...","token_type":"bearer"}

# Summarize text (requires Bearer token)
curl -X POST $BASE/api/v1/summarize/text \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"text":"Your long text here...","format":"paragraph","length":"medium"}'

# List past summaries
curl $BASE/api/v1/history/summaries \
  -H "Authorization: Bearer <access_token>"

# Start or continue a chat session
curl -X POST $BASE/api/v1/chat \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"summary_id":"<uuid>","message":"What are the key points?"}'

# Download summary as PDF
curl $BASE/api/v1/export/<summary_id> \
  -H "Authorization: Bearer <access_token>" \
  --output summary.pdf

# Refresh tokens
curl -X POST $BASE/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

## Quick Start (Local Development)

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
