"""
Shared test fixtures and configuration.

Provides:
- In-memory SQLite database for isolated testing
- Mock OpenAI client for agent tests
- Test data factories
"""

import os
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base

# Set test environment variables before any app imports
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
os.environ.setdefault("MY_EMAIL", "test@example.com")
os.environ.setdefault("APP_PASSWORD", "test-password")
os.environ.setdefault("POSTGRES_HOST", "localhost")


@pytest.fixture
def test_db():
    """
    Create an in-memory SQLite database for testing.

    Each test gets a fresh database with all tables created.
    The session is rolled back after each test for isolation.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def repository(test_db):
    """Create a Repository instance backed by the test database."""
    from app.database.repository import Repository
    return Repository(session=test_db)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client that returns predictable responses."""
    mock_client = MagicMock()

    # Mock response for digest generation
    mock_response = MagicMock()
    mock_response.output_parsed = MagicMock()
    mock_response.output_parsed.title = "Test Digest Title"
    mock_response.output_parsed.summary = "Test digest summary for testing purposes."

    mock_client.responses.parse.return_value = mock_response

    return mock_client


@pytest.fixture
def sample_youtube_video():
    """Sample YouTube video data for testing."""
    return {
        "video_id": "test_video_123",
        "title": "GPT-5 Released: Everything You Need to Know",
        "url": "https://www.youtube.com/watch?v=test_video_123",
        "channel_id": "UCtest123",
        "published_at": datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc),
        "description": "A comprehensive overview of GPT-5 capabilities.",
        "transcript": "Today we are going to talk about GPT-5 and its new capabilities...",
    }


@pytest.fixture
def sample_openai_article():
    """Sample OpenAI article data for testing."""
    return {
        "guid": "openai-article-001",
        "title": "Introducing GPT-5",
        "url": "https://openai.com/blog/gpt-5",
        "published_at": datetime(2026, 6, 28, 10, 0, 0, tzinfo=timezone.utc),
        "description": "We are excited to announce GPT-5...",
        "category": "announcements",
    }


@pytest.fixture
def sample_anthropic_article():
    """Sample Anthropic article data for testing."""
    return {
        "guid": "anthropic-article-001",
        "title": "New Research on AI Safety",
        "url": "https://anthropic.com/research/safety",
        "published_at": datetime(2026, 6, 28, 9, 0, 0, tzinfo=timezone.utc),
        "description": "Our latest research on AI alignment...",
        "category": "research",
    }


@pytest.fixture
def sample_scraped_item():
    """Sample ScrapedItem data for the universal scraped_content table."""
    return {
        "source_id": "arxiv-2026-12345",
        "source_type": "arxiv",
        "title": "Attention Is Still All You Need: Revisiting Transformer Architecture",
        "url": "https://arxiv.org/abs/2026.12345",
        "description": "We revisit the transformer architecture...",
        "content": "We revisit the original transformer architecture and propose improvements...",
        "published_at": datetime(2026, 6, 28, 8, 0, 0, tzinfo=timezone.utc),
        "category": "cs.LG",
        "metadata": {"authors": ["John Doe", "Jane Smith"], "pdf_url": "https://arxiv.org/pdf/2026.12345"},
    }
