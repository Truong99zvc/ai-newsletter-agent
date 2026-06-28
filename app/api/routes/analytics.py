"""
Analytics endpoints.

Provides dashboard statistics, source breakdowns, and trend data.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.schemas import AnalyticsSummary, PipelineRunResponse
from app.database.connection import get_db
from app.database.repository import Repository
from app.logging_config import get_logger

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
logger = get_logger(__name__)


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    hours: int = Query(default=24, ge=1, le=720, description="Lookback window"),
    db: Session = Depends(get_db),
):
    """
    Get dashboard analytics summary.

    Returns article/digest counts, source breakdown, and latest pipeline run info.
    """
    repo = Repository(session=db)

    # Counts
    total_articles = repo.count_scraped_content()
    articles_today = repo.count_scraped_content(hours=hours)
    total_digests = repo.count_digests()
    digests_today = len(repo.get_recent_digests(hours=hours))
    source_breakdown = repo.get_source_counts(hours=hours)

    # Latest pipeline run
    latest_run_response = None
    latest_run = repo.get_latest_pipeline_run()
    if latest_run:
        latest_run_response = PipelineRunResponse(
            run_id=latest_run.id,
            status=latest_run.status,
            started_at=latest_run.started_at,
            completed_at=latest_run.completed_at,
            duration_seconds=latest_run.duration_seconds,
            articles_scraped=latest_run.articles_scraped,
            digests_created=latest_run.digests_created,
            email_sent=latest_run.email_sent,
        )

    return AnalyticsSummary(
        total_articles=total_articles,
        total_digests=total_digests,
        articles_today=articles_today,
        digests_today=digests_today,
        source_breakdown=source_breakdown,
        latest_run=latest_run_response,
    )
