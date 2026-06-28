"""
FastAPI application factory.

Creates and configures the FastAPI application with:
- CORS middleware for frontend integration
- Request logging middleware
- API route registration
- OpenAPI documentation configuration
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, pipeline, digests, sources, analytics
from app.database.models import Base
from app.database.connection import engine
from app.logging_config import setup_logging, get_logger
from app.settings import get_settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    setup_logging(level=get_settings().log_level)
    logger.info("Starting AI Newsletter Agent API...")

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified")

    yield

    logger.info("Shutting down AI Newsletter Agent API...")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns a fully configured FastAPI instance with all routes
    and middleware registered.
    """
    settings = get_settings()

    app = FastAPI(
        title="AI Newsletter Agent API",
        description=(
            "REST API for the AI Newsletter Agent — an autonomous pipeline that scrapes, "
            "summarizes, ranks, and delivers personalized AI news digests.\n\n"
            "## Features\n"
            "- 📰 Browse and search AI-generated digests\n"
            "- 🚀 Trigger and monitor pipeline runs\n"
            "- 📊 View analytics and source breakdowns\n"
            "- 🔌 Manage content sources\n"
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Alternative dev port
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register route modules
    app.include_router(health.router)
    app.include_router(pipeline.router)
    app.include_router(digests.router)
    app.include_router(sources.router)
    app.include_router(analytics.router)

    return app


# Application instance for uvicorn
app = create_app()
