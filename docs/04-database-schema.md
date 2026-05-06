# 05 — Database Schema

## Overview

PostgreSQL 15 is the single persistent store. The schema has four core tables: `users`, `summaries`, `chat_sessions`, and `chat_messages`. All IDs are UUIDs. All timestamps are stored as `TIMESTAMP WITH TIME ZONE` in UTC. Schema changes are managed exclusively through Alembic migrations — never through manual SQL.

---

## Entity Relationship Diagram

```
users
├── id (PK, UUID)
├── email (UNIQUE, NOT NULL)
├── hashed_password (NOT NULL)
├── is_active (BOOLEAN, DEFAULT true)
├── created_at
└── updated_at
         │
         │ 1 ─── N
         │
summaries
├── id (PK, UUID)
├── user_id (FK → users.id, ON DELETE CASCADE)
├── input_hash (VARCHAR 64 — SHA-256 of original text, for deduplication)
├── original_text (TEXT)
├── summary (TEXT, NOT NULL)
├── format (VARCHAR 20 — 'paragraph' | 'bullets')
├── summary_length (VARCHAR 10 — 'short' | 'medium' | 'long')
├── word_count (INTEGER)
├── language (VARCHAR 10 — ISO 639-1 code, e.g. 'en')
├── model_used (VARCHAR 50 — e.g. 'gpt-4o-mini', 'bart-large-cnn')
├── tokens_used (INTEGER)
├── keywords (JSONB — array of keyword strings)
├── source_type (VARCHAR 10 — 'text' | 'pdf')
├── original_filename (VARCHAR 255, NULLABLE — for PDF uploads)
├── created_at
└── updated_at
         │
         │ 1 ─── N
         │
chat_sessions
├── id (PK, UUID)
├── user_id (FK → users.id, ON DELETE CASCADE)
├── summary_id (FK → summaries.id, ON DELETE SET NULL, NULLABLE)
├── title (VARCHAR 255 — auto-generated from first user message)
├── created_at
└── updated_at
         │
         │ 1 ─── N
         │
chat_messages
├── id (PK, UUID)
├── session_id (FK → chat_sessions.id, ON DELETE CASCADE)
├── role (VARCHAR 20 — 'user' | 'assistant')
├── content (TEXT, NOT NULL)
├── tokens_used (INTEGER, NULLABLE)
└── created_at
```

---

## Table Definitions (DDL)

### `users`

```sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);
```

### `summaries`

```sql
CREATE TABLE summaries (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    input_hash       VARCHAR(64) NOT NULL,
    original_text    TEXT NOT NULL,
    summary          TEXT NOT NULL,
    format           VARCHAR(20) NOT NULL DEFAULT 'paragraph'
                         CHECK (format IN ('paragraph', 'bullets')),
    summary_length   VARCHAR(10) NOT NULL DEFAULT 'medium'
                         CHECK (summary_length IN ('short', 'medium', 'long')),
    word_count       INTEGER,
    language         VARCHAR(10),
    model_used       VARCHAR(50),
    tokens_used      INTEGER,
    keywords         JSONB DEFAULT '[]',
    source_type      VARCHAR(10) NOT NULL DEFAULT 'text'
                         CHECK (source_type IN ('text', 'pdf')),
    original_filename VARCHAR(255),
    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_summaries_user_id ON summaries (user_id);
CREATE INDEX idx_summaries_input_hash ON summaries (input_hash);
CREATE INDEX idx_summaries_created_at ON summaries (created_at DESC);
CREATE INDEX idx_summaries_keywords ON summaries USING GIN (keywords);
```

### `chat_sessions`

```sql
CREATE TABLE chat_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary_id  UUID REFERENCES summaries(id) ON DELETE SET NULL,
    title       VARCHAR(255) NOT NULL DEFAULT 'New Chat',
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions (user_id);
CREATE INDEX idx_chat_sessions_summary_id ON chat_sessions (summary_id);
```

### `chat_messages`

```sql
CREATE TABLE chat_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    tokens_used INTEGER,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages (session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages (created_at ASC);
```

---

## SQLAlchemy Models

### `app/db/models/base.py`

```python
import uuid
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def uuid_pk():
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

def timestamps():
    return (
        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
        Column("updated_at", DateTime(timezone=True), server_default=func.now(),
               onupdate=func.now(), nullable=False),
    )
```

### `app/db/models/user.py`

```python
from sqlalchemy import Column, String, Boolean
from .base import Base, uuid_pk

class User(Base):
    __tablename__ = "users"

    id              = uuid_pk()
    email           = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active       = Column(Boolean, nullable=False, default=True)
    # created_at and updated_at added via Alembic (server defaults)
```

### `app/db/models/summary.py`

```python
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base, uuid_pk
import uuid

class Summary(Base):
    __tablename__ = "summaries"

    id               = uuid_pk()
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    input_hash       = Column(String(64), nullable=False, index=True)
    original_text    = Column(Text, nullable=False)
    summary          = Column(Text, nullable=False)
    format           = Column(String(20), nullable=False, default="paragraph")
    summary_length   = Column(String(10), nullable=False, default="medium")
    word_count       = Column(Integer)
    language         = Column(String(10))
    model_used       = Column(String(50))
    tokens_used      = Column(Integer)
    keywords         = Column(JSONB, default=list)
    source_type      = Column(String(10), nullable=False, default="text")
    original_filename = Column(String(255))
```

---

## Alembic Migration Strategy

### Setup (Phase 1)

```bash
# Inside backend/, with venv activated
alembic init alembic

# Edit alembic/env.py to import app settings and models
# See Phase 1 implementation for the full env.py template
```

### Create a New Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "create_users"

# Always review the generated file before applying
cat alembic/versions/0001_create_users.py

# Apply
alembic upgrade head
```

### Migration Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Roll back to a specific revision
alembic downgrade <revision_id>

# Show current revision
alembic current

# Show full history
alembic history --verbose

# Generate SQL without running (for review)
alembic upgrade head --sql
```

### Migration File Naming

```
alembic/versions/
├── 0001_create_users.py
├── 0002_create_summaries.py
├── 0003_create_chat_sessions.py
└── 0004_create_chat_messages.py
```

Use numeric prefixes for clear ordering. Alembic also auto-assigns revision IDs.

---

## PostgreSQL Connection Pool (asyncpg)

```python
# app/db/session.py
import asyncpg
from app.core.config import settings

_pool: asyncpg.Pool | None = None

async def create_pool() -> asyncpg.Pool:
    global _pool
    _pool = await asyncpg.create_pool(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        min_size=settings.DB_POOL_MIN_SIZE,   # default: 2
        max_size=settings.DB_POOL_MAX_SIZE,   # default: 10
        command_timeout=60,
        server_settings={"application_name": "ai-summarization-api"},
    )
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _pool
```

---

## Data Integrity Rules

| Rule | Implementation |
|------|----------------|
| UUIDs only — no serial integers | `gen_random_uuid()` / `uuid.uuid4()` |
| Soft-delete not needed | Hard delete with CASCADE on foreign keys |
| Deduplication of same input text | `input_hash` SHA-256 index on `summaries` |
| No orphaned chat messages | `ON DELETE CASCADE` from `chat_sessions` |
| No orphaned sessions | `ON DELETE CASCADE` from `users` |
| Chat session survives summary deletion | `ON DELETE SET NULL` on `summary_id` |
| JSONB for keywords | Enables GIN index + future full-text queries |
| All times in UTC | `TIMESTAMP WITH TIME ZONE` enforces this |

---

## Indexing Strategy

| Index | Table | Column(s) | Reason |
|-------|-------|-----------|--------|
| `idx_users_email` | users | email | Login lookup |
| `idx_summaries_user_id` | summaries | user_id | User history listing |
| `idx_summaries_input_hash` | summaries | input_hash | Deduplication check |
| `idx_summaries_created_at` | summaries | created_at DESC | Paginated history ordering |
| `idx_summaries_keywords` | summaries | keywords (GIN) | Keyword search queries |
| `idx_chat_sessions_user_id` | chat_sessions | user_id | List user's sessions |
| `idx_chat_messages_session_id` | chat_messages | session_id | Load all messages for session |
| `idx_chat_messages_created_at` | chat_messages | created_at ASC | Ordered conversation replay |
