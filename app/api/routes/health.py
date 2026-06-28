"""
Health check endpoint.

Provides system status for monitoring and load balancer health checks.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import HealthResponse
from app.database.connection import get_db
from app.settings import get_settings
from app.scrapers.registry import ScraperRegistry

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    System health check.

    Returns application version, database connectivity,
    and number of registered content sources.
    """
    settings = get_settings()

    # Test database connectivity
    db_status = "connected"
    try:
        db.execute("SELECT 1")
    except Exception:
        db_status = "disconnected"

    # Count registered sources
    registry = ScraperRegistry()
    registry.auto_discover()

    return HealthResponse(
        status="ok",
        version=settings.app_version,
        sources_count=len(registry),
        database=db_status,
    )
