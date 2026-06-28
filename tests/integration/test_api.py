"""
Integration tests for the FastAPI REST API.

Tests API endpoints end-to-end using FastAPI's TestClient
with a test database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.main import create_app
from app.database.models import Base
from sqlalchemy.pool import StaticPool

from app.database.connection import get_db


@pytest.fixture
def api_db():
    """Create an in-memory database for API tests."""
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
def client(api_db):
    """Create a FastAPI test client with injected test database."""
    app = create_app()

    def override_get_db():
        try:
            yield api_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, client):
        """Should return OK status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_health_includes_source_count(self, client):
        """Should include the number of registered sources."""
        response = client.get("/health")
        data = response.json()
        assert "sources_count" in data
        assert data["sources_count"] >= 0


class TestDigestEndpoints:
    """Tests for /api/v1/digests endpoints."""

    def _seed_digests(self, db):
        """Helper to seed test digests into the database."""
        from app.database.repository import Repository

        repo = Repository(session=db)
        for i in range(5):
            repo.create_digest(
                article_type="openai" if i % 2 == 0 else "arxiv",
                article_id=f"test-{i}",
                url=f"https://test.com/{i}",
                title=f"Test Digest {i}",
                summary=f"Summary for digest {i}",
            )

    def test_list_digests_empty(self, client):
        """Should return empty list when no digests exist."""
        response = client.get("/api/v1/digests")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_digests_with_data(self, client, api_db):
        """Should return paginated digests."""
        self._seed_digests(api_db)
        response = client.get("/api/v1/digests?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 5

    def test_list_digests_filter_by_source(self, client, api_db):
        """Should filter digests by source type."""
        self._seed_digests(api_db)
        response = client.get("/api/v1/digests?source=openai")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["article_type"] == "openai"

    def test_search_digests(self, client, api_db):
        """Should search in title and summary."""
        self._seed_digests(api_db)
        response = client.get("/api/v1/digests?q=Digest+0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

    def test_get_digest_not_found(self, client):
        """Should return 404 for non-existent digest."""
        response = client.get("/api/v1/digests/nonexistent:id")
        assert response.status_code == 404

    def test_get_digest_by_id(self, client, api_db):
        """Should return a specific digest."""
        self._seed_digests(api_db)
        response = client.get("/api/v1/digests/openai:test-0")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "openai:test-0"


class TestSourceEndpoints:
    """Tests for /api/v1/sources endpoints."""

    def test_list_sources(self, client):
        """Should return list of registered sources."""
        response = client.get("/api/v1/sources")
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert data["total"] >= 0


class TestPipelineEndpoints:
    """Tests for /api/v1/pipeline endpoints."""

    def test_pipeline_history_empty(self, client):
        """Should return empty history initially."""
        response = client.get("/api/v1/pipeline/history")
        assert response.status_code == 200
        data = response.json()
        assert data["runs"] == []

    def test_pipeline_status_not_found(self, client):
        """Should return 404 for non-existent run."""
        response = client.get("/api/v1/pipeline/status/nonexistent-id")
        assert response.status_code == 404


class TestAnalyticsEndpoints:
    """Tests for /api/v1/analytics endpoints."""

    def test_analytics_summary(self, client):
        """Should return analytics summary."""
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_articles" in data
        assert "total_digests" in data
        assert "source_breakdown" in data
