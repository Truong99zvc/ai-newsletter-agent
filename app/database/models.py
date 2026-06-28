"""
Database models for the AI Newsletter Agent.

Defines all SQLAlchemy ORM models for:
- Scraped content (YouTube, OpenAI, Anthropic)
- AI-generated digests
- Pipeline run tracking
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text, Integer, Float, JSON, Enum
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class YouTubeVideo(Base):
    """YouTube video scraped from channel RSS feeds."""

    __tablename__ = "youtube_videos"

    video_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    channel_id = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False)
    description = Column(Text)
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OpenAIArticle(Base):
    """Article scraped from the OpenAI blog RSS feed."""

    __tablename__ = "openai_articles"

    guid = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    description = Column(Text)
    published_at = Column(DateTime, nullable=False)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AnthropicArticle(Base):
    """Article scraped from the Anthropic blog RSS feeds."""

    __tablename__ = "anthropic_articles"

    guid = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    description = Column(Text)
    published_at = Column(DateTime, nullable=False)
    category = Column(String, nullable=True)
    markdown = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ScrapedContent(Base):
    """
    Universal scraped content table for the plugin architecture.

    Stores content from any source using the standardized ScrapedItem format.
    This replaces source-specific tables for new scrapers while maintaining
    backward compatibility with existing source-specific tables.
    """

    __tablename__ = "scraped_content"

    id = Column(String, primary_key=True, comment="Format: {source_type}:{source_id}")
    source_type = Column(String, nullable=False, index=True, comment="Source plugin name")
    source_id = Column(String, nullable=False, comment="Source-specific unique ID")
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    description = Column(Text, default="")
    content = Column(Text, nullable=True, comment="Full content (transcript, markdown, etc.)")
    published_at = Column(DateTime, nullable=False, index=True)
    category = Column(String, nullable=True)
    metadata_json = Column(JSON, default=dict, comment="Source-specific metadata")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Digest(Base):
    """AI-generated digest/summary for a scraped content item."""

    __tablename__ = "digests"

    id = Column(String, primary_key=True)
    article_type = Column(String, nullable=False, index=True)
    article_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=True, comment="Curator-assigned relevance score")
    rank = Column(Integer, nullable=True, comment="Curator-assigned rank position")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PipelineRun(Base):
    """
    Tracks individual pipeline execution runs.

    Records the status, timing, and results of each pipeline execution
    for monitoring, debugging, and the API/dashboard.
    """

    __tablename__ = "pipeline_runs"

    id = Column(String, primary_key=True, comment="UUID for this run")
    status = Column(
        String, nullable=False, default="pending",
        comment="pending | running | success | failed"
    )
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Configuration for this run
    hours_lookback = Column(Integer, default=24)
    top_n = Column(Integer, default=10)

    # Step-by-step tracking
    steps_completed = Column(JSON, default=dict, comment="Status of each pipeline step")
    current_step = Column(String, nullable=True, comment="Currently executing step name")

    # Results
    articles_scraped = Column(Integer, default=0)
    articles_enriched = Column(Integer, default=0)
    digests_created = Column(Integer, default=0)
    email_sent = Column(String, nullable=True, default="false", comment="true | false | skipped")

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_step = Column(String, nullable=True, comment="Step where error occurred")
