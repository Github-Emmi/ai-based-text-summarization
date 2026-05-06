"""Register all exception handlers on the FastAPI application.

Every error response from this API follows the same JSON shape:
{
    "error": "ERROR_CODE",
    "message": "Human-readable description",
    "details": [],          # list of field-level errors (validation only)
    "status_code": 422,
    "request_id": "uuid"   # generated per-request for log correlation
}
"""

import uuid
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


def _error_body(
    error_code: str,
    message: str,
    status_code: int,
    details: list | None = None,
) -> dict:
    return {
        "error": error_code,
        "message": message,
        "details": details or [],
        "status_code": status_code,
        "request_id": str(uuid.uuid4()),
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI app instance."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "Application error",
            extra={"error_code": exc.error_code, "err_message": exc.message},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.error_code, exc.message, exc.status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {"field": ".".join(str(loc) for loc in err["loc"]), "msg": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_body("VALIDATION_ERROR", "Request validation failed", 422, details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("HTTP_ERROR", exc.detail or "HTTP error", exc.status_code),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log the full traceback server-side but never leak it to the client.
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred", 500),
        )
