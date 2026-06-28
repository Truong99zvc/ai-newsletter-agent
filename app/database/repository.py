"""
Data access layer for the AI Newsletter Agent.

Provides CRUD operations for all database models with:
- Duplicate detection on inserts
- Flexible querying with filters and pagination
- Support for both legacy source-specific tables and the new universal ScrapedContent table
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.database.models import (
    YouTubeVideo,
    OpenAIArticle,
    AnthropicArticle,
    ScrapedContent,
    Digest,
    PipelineRun,
)
from app.database.connection import get_session
from app.logging_config import get_logger

logger = get_logger(__name__)


class Repository:
    """
    Data access layer providing CRUD operations for all models.

    Handles duplicate detection, bulk operations, and complex queries
    across multiple content source tables.
    """

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()

    # ──────────────────────────────────────────────
    # YouTube Videos (legacy)
    # ──────────────────────────────────────────────

    def create_youtube_video(
        self,
        video_id: str,
        title: str,
        url: str,
        channel_id: str,
        published_at: datetime,
        description: str = "",
        transcript: Optional[str] = None,
    ) -> Optional[YouTubeVideo]:
        existing = self.session.query(YouTubeVideo).filter_by(video_id=video_id).first()
        if existing:
            return None
        video = YouTubeVideo(
            video_id=video_id,
            title=title,
            url=url,
            channel_id=channel_id,
            published_at=published_at,
            description=description,
            transcript=transcript,
        )
        self.session.add(video)
        self.session.commit()
        return video

    def bulk_create_youtube_videos(self, videos: List[dict]) -> int:
        new_videos = []
        for v in videos:
            existing = (
                self.session.query(YouTubeVideo)
                .filter_by(video_id=v["video_id"])
                .first()
            )
            if not existing:
                new_videos.append(
                    YouTubeVideo(
                        video_id=v["video_id"],
                        title=v["title"],
                        url=v["url"],
                        channel_id=v.get("channel_id", ""),
                        published_at=v["published_at"],
                        description=v.get("description", ""),
                        transcript=v.get("transcript"),
                    )
                )
        if new_videos:
            self.session.add_all(new_videos)
            self.session.commit()
        return len(new_videos)

    def get_youtube_videos_without_transcript(
        self, limit: Optional[int] = None
    ) -> List[YouTubeVideo]:
        query = self.session.query(YouTubeVideo).filter(
            YouTubeVideo.transcript.is_(None)
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def update_youtube_video_transcript(self, video_id: str, transcript: str) -> bool:
        video = self.session.query(YouTubeVideo).filter_by(video_id=video_id).first()
        if video:
            video.transcript = transcript
            self.session.commit()
            return True
        return False

    # ──────────────────────────────────────────────
    # OpenAI Articles (legacy)
    # ──────────────────────────────────────────────

    def create_openai_article(
        self,
        guid: str,
        title: str,
        url: str,
        published_at: datetime,
        description: str = "",
        category: Optional[str] = None,
    ) -> Optional[OpenAIArticle]:
        existing = self.session.query(OpenAIArticle).filter_by(guid=guid).first()
        if existing:
            return None
        article = OpenAIArticle(
            guid=guid,
            title=title,
            url=url,
            published_at=published_at,
            description=description,
            category=category,
        )
        self.session.add(article)
        self.session.commit()
        return article

    def bulk_create_openai_articles(self, articles: List[dict]) -> int:
        new_articles = []
        for a in articles:
            existing = (
                self.session.query(OpenAIArticle).filter_by(guid=a["guid"]).first()
            )
            if not existing:
                new_articles.append(
                    OpenAIArticle(
                        guid=a["guid"],
                        title=a["title"],
                        url=a["url"],
                        published_at=a["published_at"],
                        description=a.get("description", ""),
                        category=a.get("category"),
                    )
                )
        if new_articles:
            self.session.add_all(new_articles)
            self.session.commit()
        return len(new_articles)

    # ──────────────────────────────────────────────
    # Anthropic Articles (legacy)
    # ──────────────────────────────────────────────

    def create_anthropic_article(
        self,
        guid: str,
        title: str,
        url: str,
        published_at: datetime,
        description: str = "",
        category: Optional[str] = None,
    ) -> Optional[AnthropicArticle]:
        existing = self.session.query(AnthropicArticle).filter_by(guid=guid).first()
        if existing:
            return None
        article = AnthropicArticle(
            guid=guid,
            title=title,
            url=url,
            published_at=published_at,
            description=description,
            category=category,
        )
        self.session.add(article)
        self.session.commit()
        return article

    def bulk_create_anthropic_articles(self, articles: List[dict]) -> int:
        new_articles = []
        for a in articles:
            existing = (
                self.session.query(AnthropicArticle).filter_by(guid=a["guid"]).first()
            )
            if not existing:
                new_articles.append(
                    AnthropicArticle(
                        guid=a["guid"],
                        title=a["title"],
                        url=a["url"],
                        published_at=a["published_at"],
                        description=a.get("description", ""),
                        category=a.get("category"),
                    )
                )
        if new_articles:
            self.session.add_all(new_articles)
            self.session.commit()
        return len(new_articles)

    def get_anthropic_articles_without_markdown(
        self, limit: Optional[int] = None
    ) -> List[AnthropicArticle]:
        query = self.session.query(AnthropicArticle).filter(
            AnthropicArticle.markdown.is_(None)
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def update_anthropic_article_markdown(self, guid: str, markdown: str) -> bool:
        article = self.session.query(AnthropicArticle).filter_by(guid=guid).first()
        if article:
            article.markdown = markdown
            self.session.commit()
            return True
        return False

    # ──────────────────────────────────────────────
    # ScrapedContent (universal, plugin architecture)
    # ──────────────────────────────────────────────

    def upsert_scraped_content(self, item: Dict[str, Any]) -> bool:
        """
        Insert or skip a scraped content item (idempotent).

        Args:
            item: Dict with keys matching ScrapedContent columns.
                  Must include source_type, source_id, title, url, published_at.

        Returns:
            True if inserted, False if already exists.
        """
        content_id = f"{item['source_type']}:{item['source_id']}"
        existing = self.session.query(ScrapedContent).filter_by(id=content_id).first()
        if existing:
            return False

        content = ScrapedContent(
            id=content_id,
            source_type=item["source_type"],
            source_id=item["source_id"],
            title=item["title"],
            url=item["url"],
            description=item.get("description", ""),
            content=item.get("content"),
            published_at=item["published_at"],
            category=item.get("category"),
            metadata_json=item.get("metadata", {}),
        )
        self.session.add(content)
        self.session.commit()
        return True

    def bulk_upsert_scraped_content(self, items: List[Dict[str, Any]]) -> int:
        """Bulk insert scraped items, skipping duplicates. Returns count of new items."""
        new_count = 0
        for item in items:
            if self.upsert_scraped_content(item):
                new_count += 1
        return new_count

    def get_scraped_content_without_enrichment(
        self,
        source_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ScrapedContent]:
        """Get scraped content items that haven't been enriched yet."""
        query = self.session.query(ScrapedContent).filter(
            ScrapedContent.content.is_(None)
        )
        if source_type:
            query = query.filter(ScrapedContent.source_type == source_type)
        if limit:
            query = query.limit(limit)
        return query.all()

    def update_scraped_content(self, content_id: str, content: str) -> bool:
        """Update the content field of a scraped item after enrichment."""
        item = self.session.query(ScrapedContent).filter_by(id=content_id).first()
        if item:
            item.content = content
            self.session.commit()
            return True
        return False

    def get_recent_scraped_content(
        self,
        hours: int = 24,
        source_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ScrapedContent]:
        """Get recently scraped content with optional filtering."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = self.session.query(ScrapedContent).filter(
            ScrapedContent.published_at >= cutoff
        )
        if source_type:
            query = query.filter(ScrapedContent.source_type == source_type)
        return (
            query.order_by(ScrapedContent.published_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_scraped_content(
        self, hours: Optional[int] = None, source_type: Optional[str] = None
    ) -> int:
        """Count scraped content items with optional filters."""
        query = self.session.query(ScrapedContent)
        if hours:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = query.filter(ScrapedContent.published_at >= cutoff)
        if source_type:
            query = query.filter(ScrapedContent.source_type == source_type)
        return query.count()

    def get_source_counts(self, hours: int = 24) -> Dict[str, int]:
        """Get article count breakdown by source for the given period."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        items = (
            self.session.query(ScrapedContent)
            .filter(ScrapedContent.published_at >= cutoff)
            .all()
        )
        counts: Dict[str, int] = {}
        for item in items:
            counts[item.source_type] = counts.get(item.source_type, 0) + 1
        return counts

    # ──────────────────────────────────────────────
    # Digests
    # ──────────────────────────────────────────────

    def get_articles_without_digest(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all articles (from all sources) that don't have a digest yet."""
        articles = []
        seen_ids = set()

        digests = self.session.query(Digest).all()
        for d in digests:
            seen_ids.add(f"{d.article_type}:{d.article_id}")

        # Legacy YouTube videos
        youtube_videos = (
            self.session.query(YouTubeVideo)
            .filter(
                YouTubeVideo.transcript.isnot(None),
                YouTubeVideo.transcript != "__UNAVAILABLE__",
            )
            .all()
        )
        for video in youtube_videos:
            key = f"youtube:{video.video_id}"
            if key not in seen_ids:
                articles.append(
                    {
                        "type": "youtube",
                        "id": video.video_id,
                        "title": video.title,
                        "url": video.url,
                        "content": video.transcript or video.description or "",
                        "published_at": video.published_at,
                    }
                )

        # Legacy OpenAI articles
        openai_articles = self.session.query(OpenAIArticle).all()
        for article in openai_articles:
            key = f"openai:{article.guid}"
            if key not in seen_ids:
                articles.append(
                    {
                        "type": "openai",
                        "id": article.guid,
                        "title": article.title,
                        "url": article.url,
                        "content": article.description or "",
                        "published_at": article.published_at,
                    }
                )

        # Legacy Anthropic articles
        anthropic_articles = (
            self.session.query(AnthropicArticle)
            .filter(
                AnthropicArticle.markdown.isnot(None),
            )
            .all()
        )
        for article in anthropic_articles:
            key = f"anthropic:{article.guid}"
            if key not in seen_ids:
                articles.append(
                    {
                        "type": "anthropic",
                        "id": article.guid,
                        "title": article.title,
                        "url": article.url,
                        "content": article.markdown or article.description or "",
                        "published_at": article.published_at,
                    }
                )

        # New universal scraped_content table
        scraped_items = (
            self.session.query(ScrapedContent)
            .filter(
                ScrapedContent.content.isnot(None),
            )
            .all()
        )
        for item in scraped_items:
            key = f"{item.source_type}:{item.source_id}"
            if key not in seen_ids:
                articles.append(
                    {
                        "type": item.source_type,
                        "id": item.source_id,
                        "title": item.title,
                        "url": item.url,
                        "content": item.content or item.description or "",
                        "published_at": item.published_at,
                    }
                )

        if limit:
            articles = articles[:limit]

        return articles

    def create_digest(
        self,
        article_type: str,
        article_id: str,
        url: str,
        title: str,
        summary: str,
        published_at: Optional[datetime] = None,
    ) -> Optional[Digest]:
        digest_id = f"{article_type}:{article_id}"
        existing = self.session.query(Digest).filter_by(id=digest_id).first()
        if existing:
            return None

        if published_at:
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)
            created_at = published_at
        else:
            created_at = datetime.now(timezone.utc)

        digest = Digest(
            id=digest_id,
            article_type=article_type,
            article_id=article_id,
            url=url,
            title=title,
            summary=summary,
            created_at=created_at,
        )
        self.session.add(digest)
        self.session.commit()
        return digest

    def get_recent_digests(self, hours: int = 24) -> List[Dict[str, Any]]:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        digests = (
            self.session.query(Digest)
            .filter(
                Digest.created_at >= cutoff_time,
            )
            .order_by(Digest.created_at.desc())
            .all()
        )

        return [
            {
                "id": d.id,
                "article_type": d.article_type,
                "article_id": d.article_id,
                "url": d.url,
                "title": d.title,
                "summary": d.summary,
                "relevance_score": d.relevance_score,
                "rank": d.rank,
                "created_at": d.created_at,
            }
            for d in digests
        ]

    def get_digest_by_id(self, digest_id: str) -> Optional[Digest]:
        return self.session.query(Digest).filter_by(id=digest_id).first()

    def get_digests_paginated(
        self,
        limit: int = 20,
        offset: int = 0,
        source_type: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[Digest]:
        """Get digests with pagination, optional source filter, and text search."""
        query = self.session.query(Digest)
        if source_type:
            query = query.filter(Digest.article_type == source_type)
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                Digest.title.ilike(search_pattern)
                | Digest.summary.ilike(search_pattern)
            )
        return (
            query.order_by(Digest.created_at.desc()).offset(offset).limit(limit).all()
        )

    def count_digests(self, source_type: Optional[str] = None) -> int:
        query = self.session.query(Digest)
        if source_type:
            query = query.filter(Digest.article_type == source_type)
        return query.count()

    def update_digest_ranking(self, digest_id: str, score: float, rank: int) -> bool:
        """Update the relevance score and rank for a digest after curation."""
        digest = self.session.query(Digest).filter_by(id=digest_id).first()
        if digest:
            digest.relevance_score = score
            digest.rank = rank
            self.session.commit()
            return True
        return False

    # ──────────────────────────────────────────────
    # Pipeline Runs
    # ──────────────────────────────────────────────

    def create_pipeline_run(self, hours: int = 24, top_n: int = 10) -> PipelineRun:
        """Create a new pipeline run record."""
        run = PipelineRun(
            id=str(uuid4()),
            status="pending",
            hours_lookback=hours,
            top_n=top_n,
        )
        self.session.add(run)
        self.session.commit()
        return run

    def update_pipeline_run(self, run_id: str, **kwargs) -> bool:
        """Update a pipeline run with given fields."""
        run = self.session.query(PipelineRun).filter_by(id=run_id).first()
        if not run:
            return False
        for key, value in kwargs.items():
            if hasattr(run, key):
                setattr(run, key, value)
        self.session.commit()
        return True

    def get_pipeline_run(self, run_id: str) -> Optional[PipelineRun]:
        return self.session.query(PipelineRun).filter_by(id=run_id).first()

    def get_pipeline_runs(self, limit: int = 20) -> List[PipelineRun]:
        return (
            self.session.query(PipelineRun)
            .order_by(PipelineRun.started_at.desc())
            .limit(limit)
            .all()
        )

    def get_latest_pipeline_run(self) -> Optional[PipelineRun]:
        return (
            self.session.query(PipelineRun)
            .order_by(PipelineRun.started_at.desc())
            .first()
        )
