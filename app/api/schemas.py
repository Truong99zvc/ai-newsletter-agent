"""
Pydantic schemas for API request/response models.

Separates API contract from database models, enabling
independent evolution of the API surface and internal data structures.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Common
# ──────────────────────────────────────────────


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel):
    """Wrapper for paginated list responses."""

    items: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool


# ──────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    sources_count: int
    database: str = "connected"


# ──────────────────────────────────────────────
# Pipeline
# ──────────────────────────────────────────────


class PipelineRunRequest(BaseModel):
    """Request body for triggering a pipeline run."""

    hours: int = Field(default=24, ge=1, le=168, description="Lookback window in hours")
    top_n: int = Field(default=10, ge=1, le=50, description="Number of top articles")
    send_email: bool = Field(default=True, description="Whether to send email")


class PipelineStepStatus(BaseModel):
    """Status of a single pipeline step."""

    status: str
    detail: Optional[Dict[str, Any]] = None


class PipelineRunResponse(BaseModel):
    """Response for a pipeline run."""

    run_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    hours_lookback: int = 24
    top_n: int = 10
    current_step: Optional[str] = None
    steps_completed: Optional[Dict[str, str]] = None
    articles_scraped: int = 0
    articles_enriched: int = 0
    digests_created: int = 0
    email_sent: Optional[str] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class PipelineRunListResponse(BaseModel):
    """Response for listing pipeline runs."""

    runs: List[PipelineRunResponse]
    total: int


# ──────────────────────────────────────────────
# Digests
# ──────────────────────────────────────────────


class DigestResponse(BaseModel):
    """Response for a single digest."""

    id: str
    article_type: str
    article_id: str
    url: str
    title: str
    summary: str
    relevance_score: Optional[float] = None
    rank: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DigestListResponse(BaseModel):
    """Paginated list of digests."""

    items: List[DigestResponse]
    total: int
    limit: int
    offset: int


class DigestSearchRequest(BaseModel):
    """Search parameters for digests."""

    query: str = Field(min_length=1, max_length=200)
    source_type: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# ──────────────────────────────────────────────
# Sources
# ──────────────────────────────────────────────


class SourceInfo(BaseModel):
    """Information about a registered scraper source."""

    name: str
    display_name: str
    type: str
    extra: Optional[Dict[str, Any]] = None


class SourceListResponse(BaseModel):
    """List of all registered sources."""

    sources: List[SourceInfo]
    total: int


# ──────────────────────────────────────────────
# Analytics
# ──────────────────────────────────────────────


class AnalyticsSummary(BaseModel):
    """Dashboard analytics summary."""

    total_articles: int
    total_digests: int
    articles_today: int
    digests_today: int
    source_breakdown: Dict[str, int]
    latest_run: Optional[PipelineRunResponse] = None


class TrendDataPoint(BaseModel):
    """Single data point in a trend chart."""

    date: str
    count: int
    source: Optional[str] = None


class TrendsResponse(BaseModel):
    """Trend data for analytics charts."""

    data: List[TrendDataPoint]
    period_days: int
