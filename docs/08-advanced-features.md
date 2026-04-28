# 08 — Advanced Features

## Overview

Phase 3 extends the core summarization API with six advanced capabilities: JWT authentication, chat-with-document, chat history persistence, keyword extraction, multi-language summarization, and PDF export. Each feature is implemented as a self-contained service with its own repository and route.

---

## Feature 1 — JWT Authentication

### Design

- Stateless JWT tokens (no server-side session store)
- Access token: 30 minutes (configurable)
- Refresh token: 7 days (configurable)
- Bcrypt password hashing with cost factor 12
- All `/api/v1/*` routes protected via FastAPI `Depends(get_current_user)`

### Implementation (`app/core/security.py`)

```python
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "access"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
```

### Auth Dependency (`app/core/dependencies.py`)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token
from app.db.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db=Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user = await UserRepository(db).get_by_id(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

### Password Policy

- Minimum 8 characters
- At least one uppercase letter
- At least one digit
- At least one special character (`!@#$%^&*`)
- Enforced via Pydantic `@field_validator` in `RegisterRequest` schema

---

## Feature 2 — Chat with Document

### Design

- Each chat session is tied to an optional `summary_id`
- The original document text and summary are injected as the system prompt context
- Conversation history is fetched and included in each new OpenAI call (sliding window)
- Context window limit: last 10 messages + system prompt to stay within GPT-4o-mini's 128k context

### Context Window Management (`app/services/chat.py`)

```python
MAX_HISTORY_MESSAGES = 10   # Last N turns included in the prompt
MAX_CONTEXT_CHARS = 8000    # Truncate original_text to this length

async def build_conversation(
    session_id: str,
    new_message: str,
    summary: Summary | None,
    db,
) -> list[dict]:
    messages = []

    # System prompt with document context
    if summary:
        system_content = build_chat_prompt(
            summary=summary.summary,
            original_text=summary.original_text[:MAX_CONTEXT_CHARS]
        )
    else:
        system_content = "You are a helpful assistant."
    messages.append({"role": "system", "content": system_content})

    # Load recent history from DB
    history = await ChatMessageRepository(db).get_recent(
        session_id=session_id, limit=MAX_HISTORY_MESSAGES
    )
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    # Add new user message
    messages.append({"role": "user", "content": new_message})
    return messages
```

### Session Auto-Title

When a new session is created, the title is auto-generated from the first user message:

```python
def auto_title(first_message: str) -> str:
    words = first_message.strip().split()
    title = " ".join(words[:8])
    return title[:255] if len(title) <= 255 else title[:252] + "..."
```

---

## Feature 3 — Chat History Persistence

Chat history is stored in two tables:
- `chat_sessions` — one row per conversation
- `chat_messages` — all messages ordered by `created_at ASC`

### Chat Message Repository (`app/db/repositories/chat_message_repository.py`)

```python
async def get_recent(self, session_id: str, limit: int = 10) -> list:
    query = """
        SELECT id, role, content, tokens_used, created_at
        FROM chat_messages
        WHERE session_id = $1
        ORDER BY created_at ASC
        LIMIT $2
    """
    rows = await self.conn.fetch(query, session_id, limit)
    return [dict(row) for row in rows]

async def create(self, session_id: str, role: str, content: str, tokens_used: int | None = None):
    query = """
        INSERT INTO chat_messages (id, session_id, role, content, tokens_used)
        VALUES (gen_random_uuid(), $1, $2, $3, $4)
        RETURNING id, created_at
    """
    return await self.conn.fetchrow(query, session_id, role, content, tokens_used)
```

---

## Feature 4 — Keyword Extraction

### Design

- KeyBERT extracts semantically meaningful keywords using BERT embeddings
- Runs after summarization on the original text
- Returns top 5-10 keywords per document
- Stored in the `keywords` JSONB column for fast retrieval and search

### Implementation (`app/services/keyword_extractor.py`)

```python
from keybert import KeyBERT
import asyncio
from functools import partial

_kw_model = None

def get_kw_model() -> KeyBERT:
    global _kw_model
    if _kw_model is None:
        _kw_model = KeyBERT()   # Uses "all-MiniLM-L6-v2" by default (~80MB)
    return _kw_model

async def extract_keywords(text: str, top_n: int = 8) -> list[str]:
    loop = asyncio.get_event_loop()
    model = get_kw_model()
    results = await loop.run_in_executor(
        None,
        partial(
            model.extract_keywords,
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words="english",
            top_n=top_n,
            diversity=0.5,
        )
    )
    return [kw for kw, _ in results]
```

**Model**: `all-MiniLM-L6-v2` (downloaded automatically by `sentence-transformers`, ~80MB)

---

## Feature 5 — Multi-Language Summarization

### Design

- Language is detected on input text using `langdetect`
- OpenAI GPT-4o-mini natively handles 50+ languages
- HuggingFace BART is English-only; if fallback is needed for non-English text, the text is translated to English first, summarized, then translated back
- Language code is stored in the `language` column (ISO 639-1, e.g., `en`, `fr`, `de`, `es`)

### Language Detection (`app/services/preprocessor.py`)

```python
from langdetect import detect, LangDetectException

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "en"   # Default to English if detection fails
```

### Prompt Language Instruction

The summarization system prompt already instructs: _"Respond in the same language as the input text"_ — so OpenAI handles this automatically.

### HuggingFace Multi-Language Handling

```python
# In ai/router.py, when falling back to HuggingFace for non-English text:
if language != "en" and not settings.OPENAI_API_KEY:
    # Translate to English via OpenAI (if key available) or skip HF
    # For now, HF handles only English input — document this limitation
    logger.warning(f"HuggingFace fallback used for language '{language}' — results may be poor")
```

> **Limitation**: The HuggingFace BART fallback is best-effort for non-English text. For production multi-language support, `OPENAI_API_KEY` should always be set.

---

## Feature 6 — Export Summary as PDF

### Design

- User calls `GET /api/v1/export/{summary_id}`
- `ExportService` builds a PDF from the summary using `reportlab`
- PDF is returned as a streaming response with correct content-type headers
- Filename: `summary-{summary_id[:8]}.pdf`

### Implementation (`app/services/export.py`)

```python
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib import colors
from app.db.models.summary import Summary

def generate_summary_pdf(summary: Summary) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], textColor=colors.HexColor("#1a1a2e"))
    story.append(Paragraph("Document Summary", title_style))
    story.append(Spacer(1, 0.2 * inch))

    # Metadata
    meta = f"Language: {summary.language.upper()} | Model: {summary.model_used} | Words: {summary.word_count}"
    story.append(Paragraph(meta, styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # Summary body
    body_style = ParagraphStyle("Body", parent=styles["Normal"], leading=16)
    for paragraph in summary.summary.split("\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), body_style))
            story.append(Spacer(1, 0.1 * inch))

    # Keywords
    if summary.keywords:
        story.append(Spacer(1, 0.2 * inch))
        kw_text = "Keywords: " + ", ".join(summary.keywords)
        story.append(Paragraph(kw_text, styles["Italic"]))

    # Footer
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"Generated: {summary.created_at.strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
```

### Route (`app/api/v1/export.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from app.core.dependencies import get_current_user, get_db
from app.db.repositories.summary_repository import SummaryRepository
from app.services.export import generate_summary_pdf

router = APIRouter(prefix="/api/v1/export", tags=["Export"])

@router.get("/{summary_id}")
async def export_summary_pdf(
    summary_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    summary = await SummaryRepository(db).get_by_id(summary_id)
    if not summary or str(summary.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Summary not found")

    pdf_bytes = generate_summary_pdf(summary)
    filename = f"summary-{str(summary_id)[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

---

## Feature Dependencies

| Feature | Python Package | pip install |
|---------|---------------|-------------|
| JWT Auth | python-jose[cryptography] | `pip install "python-jose[cryptography]"` |
| Password hashing | passlib[bcrypt] | `pip install "passlib[bcrypt]"` |
| Keyword extraction | keybert | `pip install keybert` |
| Language detection | langdetect | `pip install langdetect` |
| PDF export | reportlab | `pip install reportlab` |
| Chat context | (uses openai client) | already installed |
| Sentence transformers (KeyBERT) | sentence-transformers | `pip install sentence-transformers` |

All of these are included in `requirements.txt` starting from Phase 3.
