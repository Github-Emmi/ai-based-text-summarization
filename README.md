# AI-Based Text Summarization Platform

A production-ready FastAPI backend for AI-powered text and PDF summarization using OpenAI GPT-4o-mini and HuggingFace Transformers.

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

## Quick Start

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
