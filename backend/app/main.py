"""
Application entry point.

Creates and configures the FastAPI application instance with
middleware, routes, and startup configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import API_TITLE, API_VERSION, API_DESCRIPTION, HOST, PORT, DEBUG
from app.core.logging import logger
from app.api.routes import router


def create_app() -> FastAPI:
    """
    Application factory.

    Constructs the FastAPI app with all middleware and routes registered.
    Using a factory pattern allows easy testing and configuration swapping.
    """
    application = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
    )

    # CORS: Allow all origins in development. In production, restrict to
    # the frontend domain via environment variable.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    application.include_router(router)

    # Root endpoint
    @application.get("/")
    async def root():
        return {
            "service": API_TITLE,
            "version": API_VERSION,
            "status": "running",
            "docs": "/docs",
        }

    logger.info(f"{API_TITLE} v{API_VERSION} initialized")
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
