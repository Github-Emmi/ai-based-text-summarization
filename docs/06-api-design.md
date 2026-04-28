# 06 — API Design

## Overview

All routes follow RESTful conventions with versioned paths under `/api/v1/`. Authentication endpoints live at `/auth/`. Every response is JSON. Errors use a consistent structured format. Interactive documentation is auto-generated at `/docs` (Swagger UI) and `/redoc`.

---

## Base URL

| Environment | Base URL |
|-------------|----------|
| Local Dev | `http://localhost:8000` |
| Production | `https://ai-text-summarization.onrender.com` |

---

## Authentication

All `/api/v1/*` routes require a valid JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are obtained from `POST /auth/login`. Access tokens expire in 30 minutes. Use `POST /auth/refresh` to rotate with a refresh token.

---

## Endpoint Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Application health check |
| GET | `/health/db` | None | Database connectivity check |
| POST | `/auth/register` | None | Create new user account |
| POST | `/auth/login` | None | Login, receive JWT tokens |
| POST | `/auth/refresh` | Refresh token | Rotate access + refresh tokens |
| POST | `/api/v1/summarize/text` | Bearer | Summarize raw text input |
| POST | `/api/v1/summarize/pdf` | Bearer | Upload PDF and summarize |
| GET | `/api/v1/history/summaries` | Bearer | Paginated list of past summaries |
| GET | `/api/v1/history/summaries/{id}` | Bearer | Retrieve a single summary |
| DELETE | `/api/v1/history/summaries/{id}` | Bearer | Delete a summary |
| POST | `/api/v1/chat` | Bearer | Send a chat message to a session |
| GET | `/api/v1/chat/{session_id}` | Bearer | Retrieve full chat history |
| GET | `/api/v1/history/chats` | Bearer | List all chat sessions |
| DELETE | `/api/v1/chat/{session_id}` | Bearer | Delete a chat session |
| GET | `/api/v1/export/{summary_id}` | Bearer | Download summary as PDF |

---

## Health Endpoints

### `GET /health`

No authentication required.

**Response 200**:
```json
{
  "status": "ok",
  "environment": "development",
  "version": "1.0.0"
}
```

### `GET /health/db`

No authentication required.

**Response 200**:
```json
{
  "status": "ok",
  "database": "connected",
  "pool_size": 10,
  "pool_free": 8
}
```

**Response 503**:
```json
{
  "status": "error",
  "database": "unreachable"
}
```

---

## Auth Endpoints

### `POST /auth/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

**Validation**:
- `email`: valid email format, max 255 chars
- `password`: min 8 chars, at least one uppercase, one digit, one special character

**Response 201**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2026-04-29T12:00:00Z"
}
```

**Response 409** (email already registered):
```json
{
  "error": "CONFLICT",
  "message": "Email already registered",
  "status_code": 409
}
```

---

### `POST /auth/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

**Response 200**:
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Response 401**:
```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid email or password",
  "status_code": 401
}
```

---

### `POST /auth/refresh`

**Request Body**:
```json
{
  "refresh_token": "eyJhbGci..."
}
```

**Response 200**: Same as login response.

**Response 401**: Invalid or expired refresh token.

---

## Summarization Endpoints

### `POST /api/v1/summarize/text`

Summarize a raw text string.

**Request Body**:
```json
{
  "text": "The quick brown fox...",
  "summary_length": "medium",
  "format": "paragraph"
}
```

**Field Constraints**:
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `text` | string | Yes | min 50 chars, max 100,000 chars |
| `summary_length` | enum | No | `short` \| `medium` \| `long` (default: `medium`) |
| `format` | enum | No | `paragraph` \| `bullets` (default: `paragraph`) |

**Response 200**:
```json
{
  "id": "uuid",
  "summary": "The text discusses...",
  "format": "paragraph",
  "summary_length": "medium",
  "word_count": 120,
  "language": "en",
  "model_used": "gpt-4o-mini",
  "tokens_used": 384,
  "keywords": ["fox", "quick", "brown"],
  "source_type": "text",
  "created_at": "2026-04-29T12:00:00Z"
}
```

**Response 422** (validation error):
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Input validation failed",
  "details": [
    {"field": "text", "issue": "String too short (min 50 chars)"}
  ],
  "status_code": 422
}
```

**Response 503** (AI service unavailable):
```json
{
  "error": "AI_SERVICE_UNAVAILABLE",
  "message": "Both OpenAI and HuggingFace services are unavailable",
  "status_code": 503
}
```

---

### `POST /api/v1/summarize/pdf`

Upload a PDF file and receive a summary.

**Request**: `multipart/form-data`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `file` | UploadFile | Yes | MIME: `application/pdf`, max 20MB |
| `summary_length` | string (form field) | No | `short` \| `medium` \| `long` |
| `format` | string (form field) | No | `paragraph` \| `bullets` |

**Response 200**: Same schema as text summarization, with `source_type: "pdf"` and `original_filename` populated.

**Response 400** (not a PDF):
```json
{
  "error": "INVALID_FILE_TYPE",
  "message": "Only PDF files are accepted",
  "status_code": 400
}
```

**Response 413** (file too large):
```json
{
  "error": "FILE_TOO_LARGE",
  "message": "File exceeds maximum size of 20MB",
  "status_code": 413
}
```

**Response 422** (no extractable text):
```json
{
  "error": "PDF_EXTRACTION_FAILED",
  "message": "No readable text could be extracted from the PDF",
  "status_code": 422
}
```

---

## History Endpoints

### `GET /api/v1/history/summaries`

Paginated list of the authenticated user's summaries.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number (1-indexed) |
| `page_size` | int | 10 | Items per page (max 50) |
| `source_type` | string | — | Filter by `text` or `pdf` |

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "summary": "Short preview...",
      "format": "paragraph",
      "word_count": 120,
      "language": "en",
      "model_used": "gpt-4o-mini",
      "source_type": "text",
      "created_at": "2026-04-29T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 42,
    "total_pages": 5
  }
}
```

### `GET /api/v1/history/summaries/{summary_id}`

**Response 200**: Full summary object (same as POST response).

**Response 404**: Summary not found or belongs to another user.

### `DELETE /api/v1/history/summaries/{summary_id}`

**Response 204**: No content.

**Response 404**: Not found.

---

## Chat Endpoints

### `POST /api/v1/chat`

Send a message in the context of a document.

**Request Body**:
```json
{
  "message": "What are the key arguments in this document?",
  "session_id": "uuid-or-null",
  "summary_id": "uuid-or-null"
}
```

> If `session_id` is null, a new session is created. If `summary_id` is provided, the document context is injected into the system prompt.

**Response 200**:
```json
{
  "session_id": "uuid",
  "message_id": "uuid",
  "reply": "The document argues that...",
  "tokens_used": 256,
  "created_at": "2026-04-29T12:05:00Z"
}
```

### `GET /api/v1/chat/{session_id}`

**Response 200**:
```json
{
  "session_id": "uuid",
  "title": "Chat about Climate Report",
  "summary_id": "uuid",
  "messages": [
    {"id": "uuid", "role": "user", "content": "What are...", "created_at": "..."},
    {"id": "uuid", "role": "assistant", "content": "The document...", "created_at": "..."}
  ],
  "created_at": "2026-04-29T12:00:00Z"
}
```

### `GET /api/v1/history/chats`

Paginated list of the user's chat sessions.

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Chat about Climate Report",
      "summary_id": "uuid",
      "message_count": 6,
      "created_at": "2026-04-29T12:00:00Z",
      "updated_at": "2026-04-29T12:10:00Z"
    }
  ],
  "pagination": { "page": 1, "page_size": 10, "total_items": 3, "total_pages": 1 }
}
```

### `DELETE /api/v1/chat/{session_id}`

**Response 204**: No content.

---

## Export Endpoints

### `GET /api/v1/export/{summary_id}`

Returns a downloadable PDF file of the summary.

**Response 200**:
- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="summary-{id}.pdf"`
- Body: PDF bytes

**Response 404**: Summary not found.

---

## Error Response Schema

All errors follow this structure:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable description",
  "details": [],
  "status_code": 400,
  "request_id": "uuid"
}
```

| Error Code | HTTP Status | Trigger |
|-----------|-------------|---------|
| `VALIDATION_ERROR` | 422 | Pydantic validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT |
| `FORBIDDEN` | 403 | Valid JWT but wrong user for resource |
| `NOT_FOUND` | 404 | Resource doesn't exist |
| `CONFLICT` | 409 | Duplicate resource (email) |
| `INVALID_FILE_TYPE` | 400 | Upload is not a PDF |
| `FILE_TOO_LARGE` | 413 | Upload exceeds size limit |
| `PDF_EXTRACTION_FAILED` | 422 | No text extractable from PDF |
| `AI_SERVICE_UNAVAILABLE` | 503 | Both OpenAI and HuggingFace failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests (slowapi) |
| `INTERNAL_ERROR` | 500 | Unhandled exception |

---

## OpenAPI / Swagger

The full interactive spec is available at runtime:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **JSON Schema**: `http://localhost:8000/openapi.json`

All Pydantic request/response models are automatically reflected in the OpenAPI schema. Add `response_model=`, `responses={}`, and docstrings to route functions to enrich the generated docs.
