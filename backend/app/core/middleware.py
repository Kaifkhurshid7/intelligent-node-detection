"""
Application middleware.

Provides cross-cutting concerns like request ID tracing,
timing, and structured error handling.
"""

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Adds a unique request ID to every request for observability.

    The request ID is:
        - Generated as a UUID4 for each incoming request
        - Attached to the request state for downstream access
        - Included in the response headers (X-Request-ID)
        - Logged with timing information for performance monitoring
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"→ {response.status_code} ({duration_ms:.1f}ms)"
        )

        return response
