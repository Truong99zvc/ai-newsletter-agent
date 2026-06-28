"""
Unit tests for scraper plugins.

Tests RSS feed parsing, content extraction, and ScrapedItem construction
using mocked HTTP responses to avoid network dependencies.
"""

from datetime import datetime, timezone

import pytest

from app.scrapers.base import BaseScraper, ScrapedItem


class TestScrapedItem:
    """Tests for the universal ScrapedItem model."""

    def test_create_minimal_item(self):
        """Should create an item with minimal required fields."""
        item = ScrapedItem(
            source_id="test-001",
            source_type="test",
            title="Test Article",
            url="https://test.com/article",
            published_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
        )
        assert item.source_id == "test-001"
        assert item.content is None
        assert item.metadata == {}

    def test_create_full_item(self):
        """Should create an item with all fields populated."""
        item = ScrapedItem(
            source_id="test-002",
            source_type="arxiv",
            title="Full Paper",
            url="https://arxiv.org/abs/2026.12345",
            description="A test paper",
            content="Full paper content here",
            published_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
            category="cs.AI",
            metadata={"authors": ["Alice", "Bob"]},
        )
        assert item.content == "Full paper content here"
        assert item.metadata["authors"] == ["Alice", "Bob"]

    def test_model_copy_update(self):
        """Should create a copy with updated fields."""
        item = ScrapedItem(
            source_id="test-003",
            source_type="test",
            title="Original",
            url="https://test.com",
            published_at=datetime.now(timezone.utc),
        )
        enriched = item.model_copy(update={"content": "Enriched content"})
        assert enriched.content == "Enriched content"
        assert item.content is None  # Original unchanged


class TestBaseScraper:
    """Tests for the BaseScraper abstract class."""

    def test_cannot_instantiate_abstract(self):
        """Should not be able to instantiate BaseScraper directly."""
        with pytest.raises(TypeError):
            BaseScraper()

    def test_concrete_implementation(self):
        """Should be able to create a concrete implementation."""

        class TestScraper(BaseScraper):
            def get_source_name(self):
                return "test"

            def get_source_display_name(self):
                return "Test Source"

            def scrape(self, hours=24):
                return []

        scraper = TestScraper()
        assert scraper.get_source_name() == "test"
        assert scraper.get_source_display_name() == "Test Source"
        assert scraper.scrape() == []

    def test_default_enrich_returns_unchanged(self):
        """Default enrich() should return the item unchanged."""

        class TestScraper(BaseScraper):
            def get_source_name(self):
                return "test"

            def get_source_display_name(self):
                return "Test"

            def scrape(self, hours=24):
                return []

        scraper = TestScraper()
        item = ScrapedItem(
            source_id="x", source_type="test", title="T",
            url="http://x.com", published_at=datetime.now(timezone.utc),
        )
        result = scraper.enrich(item)
        assert result == item

    def test_source_info(self):
        """Should return correct source info dict."""

        class TestScraper(BaseScraper):
            def get_source_name(self):
                return "my_source"

            def get_source_display_name(self):
                return "My Source"

            def scrape(self, hours=24):
                return []

        scraper = TestScraper()
        info = scraper.get_source_info()
        assert info["name"] == "my_source"
        assert info["display_name"] == "My Source"
        assert info["type"] == "TestScraper"


class TestScraperRegistry:
    """Tests for the scraper registry."""

    def test_register_and_get(self):
        from app.scrapers.registry import ScraperRegistry

        class FakeScraper(BaseScraper):
            def get_source_name(self):
                return "fake"

            def get_source_display_name(self):
                return "Fake"

            def scrape(self, hours=24):
                return []

        registry = ScraperRegistry()
        scraper = FakeScraper()
        registry.register(scraper)

        assert "fake" in registry
        assert registry.get("fake") is scraper
        assert len(registry) == 1

    def test_register_duplicate_raises(self):
        from app.scrapers.registry import ScraperRegistry

        class FakeScraper(BaseScraper):
            def get_source_name(self):
                return "fake"

            def get_source_display_name(self):
                return "Fake"

            def scrape(self, hours=24):
                return []

        registry = ScraperRegistry()
        registry.register(FakeScraper())

        with pytest.raises(ValueError, match="already registered"):
            registry.register(FakeScraper())

    def test_deregister(self):
        from app.scrapers.registry import ScraperRegistry

        class FakeScraper(BaseScraper):
            def get_source_name(self):
                return "fake"

            def get_source_display_name(self):
                return "Fake"

            def scrape(self, hours=24):
                return []

        registry = ScraperRegistry()
        registry.register(FakeScraper())
        removed = registry.deregister("fake")

        assert removed is not None
        assert "fake" not in registry

    def test_get_all(self):
        from app.scrapers.registry import ScraperRegistry

        class Scraper1(BaseScraper):
            def get_source_name(self):
                return "s1"

            def get_source_display_name(self):
                return "S1"

            def scrape(self, hours=24):
                return []

        class Scraper2(BaseScraper):
            def get_source_name(self):
                return "s2"

            def get_source_display_name(self):
                return "S2"

            def scrape(self, hours=24):
                return []

        registry = ScraperRegistry()
        registry.register(Scraper1())
        registry.register(Scraper2())

        assert len(registry.get_all()) == 2
        assert set(registry.get_names()) == {"s1", "s2"}
