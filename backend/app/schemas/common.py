from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str


class HealthDBResponse(BaseModel):
    status: str
    database: str
    pool_size: int | None = None
    pool_free: int | None = None


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: list[dict[str, Any]] = []
    status_code: int
    request_id: str


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
