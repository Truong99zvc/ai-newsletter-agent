"""
Source management endpoints.

Provides API for viewing registered content sources.
"""

from fastapi import APIRouter

from app.api.schemas import SourceInfo, SourceListResponse
from app.scrapers.registry import ScraperRegistry

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.get("", response_model=SourceListResponse)
def list_sources():
    """
    List all registered content sources.

    Returns information about each scraper plugin including
    source name, display name, and type.
    """
    registry = ScraperRegistry()
    registry.auto_discover()

    sources = []
    for info in registry.get_source_info():
        sources.append(SourceInfo(
            name=info["name"],
            display_name=info["display_name"],
            type=info["type"],
            extra={k: v for k, v in info.items() if k not in ("name", "display_name", "type")},
        ))

    return SourceListResponse(sources=sources, total=len(sources))
