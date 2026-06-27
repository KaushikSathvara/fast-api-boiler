"""FastAPI application factory with lifespan, middleware, and router mounting.

This is the main entry point for the application. Uvicorn loads `app.main:app`.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.database import close_db, init_db

__all__: list[str] = ["app"]

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager — startup and shutdown hooks."""
    configure_logging(settings)
    await init_db()
    logger.info("startup_complete", project=settings.PROJECT_NAME)
    yield
    await close_db()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="Production-ready FastAPI project scaffold",
        contact={"name": "MyProject Team"},
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # ── Middleware (outermost first) ──────────────────────────
    # SecurityHeaders → RequestLogging → CORS → app
    app.add_middleware(SecurityHeadersMiddleware, debug=settings.DEBUG)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ───────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────
    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
