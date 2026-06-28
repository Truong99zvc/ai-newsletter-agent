"""
Digest endpoints.

Provides API for browsing, searching, and viewing AI-generated digests.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import DigestResponse, DigestListResponse
from app.database.connection import get_db
from app.database.repository import Repository
from app.logging_config import get_logger

router = APIRouter(prefix="/api/v1/digests", tags=["digests"])
logger = get_logger(__name__)


@router.get("", response_model=DigestListResponse)
def list_digests(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    source: Optional[str] = Query(default=None, description="Filter by source type"),
    q: Optional[str] = Query(default=None, description="Search in title and summary"),
    db: Session = Depends(get_db),
):
    """
    List digests with pagination, optional source filtering, and text search.

    Query parameters:
    - limit: Items per page (1-100, default 20)
    - offset: Skip N items (default 0)
    - source: Filter by source type (e.g., 'youtube', 'openai', 'arxiv')
    - q: Full-text search in title and summary
    """
    repo = Repository(session=db)

    digests = repo.get_digests_paginated(
        limit=limit, offset=offset,
        source_type=source, search_query=q,
    )
    total = repo.count_digests(source_type=source)

    return DigestListResponse(
        items=[
            DigestResponse(
                id=d.id, article_type=d.article_type,
                article_id=d.article_id, url=d.url,
                title=d.title, summary=d.summary,
                relevance_score=d.relevance_score,
                rank=d.rank, created_at=d.created_at,
            )
            for d in digests
        ],
        total=total, limit=limit, offset=offset,
    )


@router.get("/{digest_id}", response_model=DigestResponse)
def get_digest(digest_id: str, db: Session = Depends(get_db)):
    """Get a specific digest by ID."""
    repo = Repository(session=db)
    digest = repo.get_digest_by_id(digest_id)

    if not digest:
        raise HTTPException(status_code=404, detail=f"Digest {digest_id} not found")

    return DigestResponse(
        id=digest.id, article_type=digest.article_type,
        article_id=digest.article_id, url=digest.url,
        title=digest.title, summary=digest.summary,
        relevance_score=digest.relevance_score,
        rank=digest.rank, created_at=digest.created_at,
    )
