"""
Abstract base class for all content scrapers.

Provides a standardized interface for scraping content from any source,
enabling a plugin-based architecture where new sources can be added by
simply implementing the BaseScraper interface.

Design Pattern: Strategy + Template Method
- Each scraper is a strategy for fetching content from a specific source.
- The `scrape()` method defines the template for the scraping workflow.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ScrapedItem(BaseModel):
    """
    Universal content item returned by all scrapers.

    This is the common data structure that normalizes content from
    different sources (YouTube, blogs, papers) into a single format.
    """

    source_id: str = Field(description="Unique identifier from the source (video_id, guid, etc.)")
    source_type: str = Field(description="Source type identifier (e.g., 'youtube', 'openai', 'arxiv')")
    title: str = Field(description="Content title")
    url: str = Field(description="Link to the original content")
    description: str = Field(default="", description="Short description or excerpt")
    content: Optional[str] = Field(default=None, description="Full content text (transcript, markdown, etc.)")
    published_at: datetime = Field(description="Publication timestamp")
    category: Optional[str] = Field(default=None, description="Content category or tag")
    metadata: dict = Field(default_factory=dict, description="Source-specific metadata")


class BaseScraper(ABC):
    """
    Abstract base class for content scrapers.

    To add a new source, create a new class that inherits from BaseScraper
    and implement all abstract methods. Then register it in the scraper registry.

    Example:
        class MyBlogScraper(BaseScraper):
            def get_source_name(self) -> str:
                return "my_blog"

            def get_source_display_name(self) -> str:
                return "My Blog"

            def scrape(self, hours: int = 24) -> List[ScrapedItem]:
                # Fetch and return items from your source
                ...

            def enrich(self, item: ScrapedItem) -> ScrapedItem:
                # Optionally fetch full content for an item
                return item
    """

    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return a unique, lowercase identifier for this source.
        Used as the source_type in ScrapedItem and database keys.
        E.g., 'youtube', 'openai', 'arxiv'
        """
        ...

    @abstractmethod
    def get_source_display_name(self) -> str:
        """
        Return a human-readable display name for this source.
        Used in UI, emails, and logs.
        E.g., 'YouTube', 'OpenAI Blog', 'arXiv Papers'
        """
        ...

    @abstractmethod
    def scrape(self, hours: int = 24) -> List[ScrapedItem]:
        """
        Scrape recent content from this source.

        Args:
            hours: Lookback window in hours. Only return items
                   published within the last `hours` hours.

        Returns:
            List of ScrapedItem objects with at least source_id,
            source_type, title, url, and published_at filled in.
        """
        ...

    def enrich(self, item: ScrapedItem) -> ScrapedItem:
        """
        Enrich a scraped item with additional content.

        Override this method to fetch full article text, transcripts,
        or other detailed content that wasn't available during scraping.

        Default implementation returns the item unchanged.

        Args:
            item: A previously scraped item to enrich.

        Returns:
            The enriched item with content field populated.
        """
        return item

    def get_source_info(self) -> dict:
        """Return metadata about this scraper for the API/UI."""
        return {
            "name": self.get_source_name(),
            "display_name": self.get_source_display_name(),
            "type": self.__class__.__name__,
        }
