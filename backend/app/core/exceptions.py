"""
Custom exception hierarchy.

Provides structured error types that map cleanly to HTTP status codes,
enabling consistent error handling across the application.
"""


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationError(AppError):
    """Input validation failure (400)."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class FileProcessingError(AppError):
    """Image loading or processing failure (422)."""

    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class PipelineError(AppError):
    """Internal pipeline stage failure (500)."""

    def __init__(self, message: str, stage: str = "unknown"):
        self.stage = stage
        super().__init__(f"Pipeline failed at stage '{stage}': {message}", status_code=500)


class ResourceNotFoundError(AppError):
    """Requested resource does not exist (404)."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} '{identifier}' not found", status_code=404)
