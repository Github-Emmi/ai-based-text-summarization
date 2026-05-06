"""Custom exception classes for the AI-Based Text Summarization API.

Each exception maps to an HTTP status code and a machine-readable error code
string used in structured JSON error responses.
"""


class AppError(Exception):
    """Base class for all application exceptions."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "An unexpected error occurred") -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message)


class UnauthorizedError(AppError):
    status_code = 401
    error_code = "UNAUTHORIZED"

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message)


class ForbiddenError(AppError):
    status_code = 403
    error_code = "FORBIDDEN"

    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message)


class ConflictError(AppError):
    status_code = 409
    error_code = "CONFLICT"

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message)


class InvalidFileTypeError(AppError):
    status_code = 400
    error_code = "INVALID_FILE_TYPE"

    def __init__(self, message: str = "Only PDF files are accepted") -> None:
        super().__init__(message)


class FileTooLargeError(AppError):
    status_code = 413
    error_code = "FILE_TOO_LARGE"

    def __init__(self, message: str = "File exceeds maximum allowed size") -> None:
        super().__init__(message)


class PDFExtractionError(AppError):
    status_code = 422
    error_code = "PDF_EXTRACTION_FAILED"

    def __init__(self, message: str = "No readable text could be extracted from the PDF") -> None:
        super().__init__(message)


class AIServiceUnavailableError(AppError):
    status_code = 503
    error_code = "AI_SERVICE_UNAVAILABLE"

    def __init__(self, message: str = "Both OpenAI and HuggingFace services are unavailable") -> None:
        super().__init__(message)
