"""
Unit tests for the database repository.

Tests CRUD operations, duplicate detection, pagination,
and search functionality using an in-memory SQLite database.
"""

from datetime import datetime, timedelta, timezone

import pytest


class TestYouTubeVideoRepository:
    """Tests for YouTube video CRUD operations."""

    def test_create_youtube_video(self, repository, sample_youtube_video):
        """Should create a new video and return it."""
        video = repository.create_youtube_video(**sample_youtube_video)
        assert video is not None
        assert video.video_id == sample_youtube_video["video_id"]
        assert video.title == sample_youtube_video["title"]

    def test_create_duplicate_youtube_video_returns_none(self, repository, sample_youtube_video):
        """Should return None when inserting a duplicate video."""
        repository.create_youtube_video(**sample_youtube_video)
        duplicate = repository.create_youtube_video(**sample_youtube_video)
        assert duplicate is None

    def test_bulk_create_youtube_videos(self, repository):
        """Should bulk insert videos and skip duplicates."""
        videos = [
            {
                "video_id": f"vid_{i}",
                "title": f"Video {i}",
                "url": f"https://youtube.com/watch?v=vid_{i}",
                "channel_id": "UCtest",
                "published_at": datetime(2026, 6, 28, tzinfo=timezone.utc),
            }
            for i in range(3)
        ]
        count = repository.bulk_create_youtube_videos(videos)
        assert count == 3

        # Insert again — should skip all
        count_dup = repository.bulk_create_youtube_videos(videos)
        assert count_dup == 0

    def test_get_videos_without_transcript(self, repository):
        """Should return only videos with no transcript."""
        repository.create_youtube_video(
            video_id="vid_1", title="Has transcript", url="http://yt.com/1",
            channel_id="UC1", published_at=datetime.now(timezone.utc),
            transcript="Some transcript text",
        )
        repository.create_youtube_video(
            video_id="vid_2", title="No transcript", url="http://yt.com/2",
            channel_id="UC1", published_at=datetime.now(timezone.utc),
        )
        videos = repository.get_youtube_videos_without_transcript()
        assert len(videos) == 1
        assert videos[0].video_id == "vid_2"

    def test_update_transcript(self, repository, sample_youtube_video):
        """Should update the transcript for a video."""
        del sample_youtube_video["transcript"]
        repository.create_youtube_video(**sample_youtube_video)
        result = repository.update_youtube_video_transcript(
            sample_youtube_video["video_id"], "Updated transcript"
        )
        assert result is True


class TestOpenAIArticleRepository:
    """Tests for OpenAI article CRUD operations."""

    def test_create_openai_article(self, repository, sample_openai_article):
        """Should create a new article."""
        article = repository.create_openai_article(**sample_openai_article)
        assert article is not None
        assert article.guid == sample_openai_article["guid"]

    def test_duplicate_detection(self, repository, sample_openai_article):
        """Should prevent duplicate articles."""
        repository.create_openai_article(**sample_openai_article)
        duplicate = repository.create_openai_article(**sample_openai_article)
        assert duplicate is None


class TestAnthropicArticleRepository:
    """Tests for Anthropic article CRUD operations."""

    def test_create_anthropic_article(self, repository, sample_anthropic_article):
        """Should create a new article."""
        article = repository.create_anthropic_article(**sample_anthropic_article)
        assert article is not None
        assert article.guid == sample_anthropic_article["guid"]

    def test_get_articles_without_markdown(self, repository, sample_anthropic_article):
        """Should return only articles without markdown content."""
        repository.create_anthropic_article(**sample_anthropic_article)
        articles = repository.get_anthropic_articles_without_markdown()
        assert len(articles) == 1

    def test_update_markdown(self, repository, sample_anthropic_article):
        """Should update the markdown field."""
        repository.create_anthropic_article(**sample_anthropic_article)
        result = repository.update_anthropic_article_markdown(
            sample_anthropic_article["guid"], "# Full Article Content"
        )
        assert result is True


class TestScrapedContentRepository:
    """Tests for the universal ScrapedContent table."""

    def test_upsert_new_item(self, repository, sample_scraped_item):
        """Should insert a new scraped item."""
        result = repository.upsert_scraped_content(sample_scraped_item)
        assert result is True

    def test_upsert_duplicate_returns_false(self, repository, sample_scraped_item):
        """Should return False for duplicate items."""
        repository.upsert_scraped_content(sample_scraped_item)
        result = repository.upsert_scraped_content(sample_scraped_item)
        assert result is False

    def test_bulk_upsert(self, repository):
        """Should bulk insert and return count of new items."""
        items = [
            {
                "source_id": f"item_{i}",
                "source_type": "arxiv",
                "title": f"Paper {i}",
                "url": f"https://arxiv.org/abs/{i}",
                "published_at": datetime.now(timezone.utc),
            }
            for i in range(5)
        ]
        count = repository.bulk_upsert_scraped_content(items)
        assert count == 5

    def test_get_without_enrichment(self, repository):
        """Should return items where content is None."""
        repository.upsert_scraped_content({
            "source_id": "enriched", "source_type": "test",
            "title": "Enriched", "url": "http://test.com/1",
            "content": "Has content",
            "published_at": datetime.now(timezone.utc),
        })
        repository.upsert_scraped_content({
            "source_id": "not_enriched", "source_type": "test",
            "title": "Not enriched", "url": "http://test.com/2",
            "published_at": datetime.now(timezone.utc),
        })
        items = repository.get_scraped_content_without_enrichment()
        assert len(items) == 1
        assert items[0].source_id == "not_enriched"


class TestDigestRepository:
    """Tests for digest CRUD operations."""

    def test_create_digest(self, repository):
        """Should create a new digest."""
        digest = repository.create_digest(
            article_type="openai", article_id="test-001",
            url="http://test.com", title="Test Digest",
            summary="This is a test summary.",
        )
        assert digest is not None
        assert digest.id == "openai:test-001"

    def test_duplicate_digest_returns_none(self, repository):
        """Should prevent duplicate digests."""
        repository.create_digest(
            article_type="openai", article_id="test-001",
            url="http://test.com", title="Test",
            summary="Summary",
        )
        duplicate = repository.create_digest(
            article_type="openai", article_id="test-001",
            url="http://test.com", title="Test",
            summary="Summary",
        )
        assert duplicate is None

    def test_get_recent_digests(self, repository):
        """Should return digests from the specified time window."""
        # Create a recent digest
        repository.create_digest(
            article_type="openai", article_id="recent",
            url="http://test.com/recent", title="Recent",
            summary="Recent article",
        )
        digests = repository.get_recent_digests(hours=24)
        assert len(digests) >= 1
        assert digests[0]["id"] == "openai:recent"

    def test_get_digests_paginated(self, repository):
        """Should support pagination."""
        for i in range(5):
            repository.create_digest(
                article_type="openai", article_id=f"page-{i}",
                url=f"http://test.com/{i}", title=f"Digest {i}",
                summary=f"Summary {i}",
            )
        page1 = repository.get_digests_paginated(limit=2, offset=0)
        page2 = repository.get_digests_paginated(limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2

    def test_search_digests(self, repository):
        """Should search in title and summary."""
        repository.create_digest(
            article_type="openai", article_id="s-1",
            url="http://test.com/1", title="GPT-5 Released",
            summary="OpenAI announces GPT-5 with improved reasoning.",
        )
        repository.create_digest(
            article_type="anthropic", article_id="s-2",
            url="http://test.com/2", title="Claude 4 Safety Report",
            summary="Anthropic publishes new safety benchmarks.",
        )
        results = repository.get_digests_paginated(search_query="GPT-5")
        assert len(results) == 1
        assert results[0].title == "GPT-5 Released"

    def test_update_ranking(self, repository):
        """Should update relevance_score and rank."""
        repository.create_digest(
            article_type="openai", article_id="rank-test",
            url="http://test.com", title="Rank Test",
            summary="Summary",
        )
        result = repository.update_digest_ranking("openai:rank-test", score=8.5, rank=1)
        assert result is True


class TestPipelineRunRepository:
    """Tests for pipeline run tracking."""

    def test_create_pipeline_run(self, repository):
        """Should create a new pipeline run."""
        run = repository.create_pipeline_run(hours=24, top_n=10)
        assert run is not None
        assert run.status == "pending"
        assert run.hours_lookback == 24

    def test_update_pipeline_run(self, repository):
        """Should update run fields."""
        run = repository.create_pipeline_run()
        result = repository.update_pipeline_run(
            run.id, status="running", current_step="scrape"
        )
        assert result is True

    def test_get_pipeline_runs(self, repository):
        """Should return runs in descending order."""
        for i in range(3):
            repository.create_pipeline_run()
        runs = repository.get_pipeline_runs(limit=10)
        assert len(runs) == 3

    def test_get_latest_pipeline_run(self, repository):
        """Should return the most recent run."""
        repository.create_pipeline_run(hours=24)
        repository.create_pipeline_run(hours=48)
        latest = repository.get_latest_pipeline_run()
        assert latest is not None
        assert latest.hours_lookback == 48
