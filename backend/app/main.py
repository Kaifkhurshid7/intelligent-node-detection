"""
Application entry point.

Creates and configures the FastAPI application with:
    - CORS middleware for cross-origin requests
    - Request tracing middleware for observability
    - Global exception handlers for consistent error responses
    - API versioning via router prefix
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import API_TITLE, API_VERSION, API_DESCRIPTION, HOST, PORT, DEBUG
from app.core.logging import logger
from app.core.exceptions import AppError
from app.core.middleware import RequestTracingMiddleware
from app.api.routes import router
from app.api.ai_routes import ai_router


def create_app() -> FastAPI:
    """
    Application factory.

    Constructs the FastAPI app with all middleware, exception handlers,
    and routes registered. Factory pattern enables easy testing with
    different configurations.
    """
    application = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # --- Middleware (executed in reverse order of registration) ---

    # CORS: Allow all origins in development.
    # Production should restrict via ALLOWED_ORIGINS env var.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request tracing: adds X-Request-ID and X-Response-Time headers
    application.add_middleware(RequestTracingMiddleware)

    # --- Exception Handlers ---

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle all custom application errors with consistent format."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "error": exc.__class__.__name__,
                "request_id": request_id,
            },
        )

    @application.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unexpected errors. Logs full traceback."""
        request_id = getattr(request.state, "request_id", None)
        logger.error(f"[{request_id}] Unhandled error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "error": "InternalError",
                "request_id": request_id,
            },
        )

    # --- Routes ---

    # API v1 routes with prefix
    application.include_router(router, prefix="/api/v1", tags=["v1"])
    application.include_router(ai_router, prefix="/api/v1", tags=["ai"])

    # Also mount at root for backward compatibility
    application.include_router(router)
    application.include_router(ai_router)

    # Root endpoint
    @application.get("/", tags=["system"])
    async def root():
        return {
            "service": API_TITLE,
            "version": API_VERSION,
            "status": "running",
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "analyze": "/analyze",
                "api_v1": "/api/v1",
            },
        }

    logger.info(f"{API_TITLE} v{API_VERSION} initialized (debug={DEBUG})")
    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
    )
