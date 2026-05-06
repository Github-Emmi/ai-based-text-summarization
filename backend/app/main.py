"""FastAPI application factory.

Responsibilities (from docs/04-project-structure.md):
  1. Create FastAPI instance with title, version, description.
  2. Register lifespan (startup: open DB pool; shutdown: close pool).
  3. Add CORSMiddleware with settings.cors_origins_list.
  4. Register exception handlers.
  5. Include routers (Phase 1: health only; later phases add /api/v1/* routes).

/health and /health/db are registered directly on the app (not under /api/v1/)
because they require no authentication and are polled by Render's health check.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.limiter import limiter
from app.core.logging import setup_logging
from app.db.session import close_pool, create_pool, get_pool
from app.schemas.common import HealthDBResponse, HealthResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown lifecycle events."""
    # ── Startup ─────────────────────────────────────────────────────────────
    setup_logging()
    logger.info("Starting AI-Based Text Summarization API", extra={"version": settings.APP_VERSION})
    app.state.pool = await create_pool()

    yield  # Application runs here

    # ── Shutdown ─────────────────────────────────────────────────────────────
    await close_pool()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Application factory. Returns a configured FastAPI instance.

    Called at module level so uvicorn can import `app` directly:
        uvicorn app.main:app
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-ready API for AI-powered text and PDF summarization "
            "using OpenAI GPT-4o-mini and HuggingFace BART."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Rate limiter (SEC-08) ─────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── Exception handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routes ───────────────────────────────────────────────────────────────
    _register_health_routes(app)

    # Phase 2: auth + users
    from app.api.v1.auth import router as auth_router
    from app.api.v1.users import router as users_router
    app.include_router(auth_router)                    # /auth/*
    app.include_router(users_router, prefix="/api/v1") # /api/v1/users/*

    # Phase 3: summarize, history, chat, export
    from app.api.v1.summarize import router as summarize_router
    from app.api.v1.history import router as history_router
    from app.api.v1.chat import router as chat_router
    from app.api.v1.export import router as export_router
    app.include_router(summarize_router, prefix="/api/v1")  # /api/v1/summarize/*
    app.include_router(history_router, prefix="/api/v1")    # /api/v1/history/*
    app.include_router(chat_router, prefix="/api/v1")       # /api/v1/chat/*
    app.include_router(export_router, prefix="/api/v1")     # /api/v1/export/*

    return app


def _register_health_routes(app: FastAPI) -> None:
    """Register /health and /health/db directly on the app (no auth required)."""

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["health"],
        summary="Application health check",
    )
    async def health() -> HealthResponse:
        """
        Returns the application status, environment, and version.
        No authentication required. Polled by Render health checker.
        """
        return HealthResponse(
            status="ok",
            environment=settings.ENVIRONMENT,
            version=settings.APP_VERSION,
        )

    @app.get(
        "/health/db",
        response_model=HealthDBResponse,
        tags=["health"],
        summary="Database connectivity check",
    )
    async def health_db() -> JSONResponse:
        """
        Runs a lightweight SELECT 1 query against PostgreSQL and reports
        the current pool size and idle connection count.
        Returns 503 if the database is unreachable.

        Uses a flag-then-return pattern to avoid constructing a JSONResponse
        inside an active except block — which triggers a MemoryError in
        Python 3.14's C JSON encoder due to exception chaining context.
        """
        _error: str | None = None
        _pool = None

        try:
            _pool = get_pool()
            async with _pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
        except Exception as exc:
            logger.error("Database health check failed", extra={"error": str(exc)})
            _error = str(exc)

        # Construct the response OUTSIDE the except block to avoid Python 3.14
        # C-json MemoryError triggered by exception chaining context.
        if _error is not None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "error", "database": "unreachable"},
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "database": "connected",
                "pool_size": _pool.get_size(),
                "pool_free": _pool.get_idle_size(),
            },
        )


# Module-level app instance — imported by uvicorn and tests.
app = create_app()
