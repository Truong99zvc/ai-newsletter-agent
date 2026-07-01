import os
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set environment variables BEFORE importing any app modules to prevent connecting to Postgres
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["OPENAI_API_KEY"] = "test-key-not-real"
os.environ["MY_EMAIL"] = "test@example.com"
os.environ["APP_PASSWORD"] = "test-password"
os.environ["ENVIRONMENT"] = "LOCAL"

from app.database.models import Base


@pytest.fixture
def test_db():
    """
    Create an in-memory SQLite database for testing.
    Initializes all schemas and provides a session.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
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
    """Mock OpenAI client returning structured outputs for test cases."""
    mock_client = MagicMock()

    # Mock response object
    mock_response = MagicMock()
    mock_client.responses.parse.return_value = mock_response

    return mock_client


@pytest.fixture
def sample_youtube_video():
    return {
        "video_id": "test_video_123",
        "title": "Test YouTube Video",
        "url": "https://youtube.com/watch?v=test_video_123",
        "channel_id": "UCtest123",
        "published_at": datetime.now(timezone.utc) - timedelta(hours=2),
        "description": "Video description",
        "transcript": "Hello this is a transcript...",
    }


@pytest.fixture
def sample_openai_article():
    return {
        "guid": "openai-article-1",
        "title": "OpenAI Release Details",
        "url": "https://openai.com/news/article-1",
        "published_at": datetime.now(timezone.utc) - timedelta(hours=3),
        "description": "Article description",
        "category": "announcements",
    }


@pytest.fixture
def sample_anthropic_article():
    return {
        "guid": "anthropic-article-1",
        "title": "Anthropic Model Release",
        "url": "https://anthropic.com/news/article-1",
        "published_at": datetime.now(timezone.utc) - timedelta(hours=4),
        "description": "Article description",
        "category": "research",
    }
