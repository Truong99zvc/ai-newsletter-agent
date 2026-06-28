"""
Scraper registry for auto-discovery and management of content sources.

The registry provides:
- Automatic discovery of all BaseScraper implementations
- Central access point for the pipeline to get all scrapers
- Runtime registration/deregistration of sources
- Source metadata for the API/UI

Usage:
    from app.scrapers.registry import ScraperRegistry

    registry = ScraperRegistry()
    registry.auto_discover()

    for scraper in registry.get_all():
        items = scraper.scrape(hours=24)
"""

from typing import Dict, List, Optional

from app.logging_config import get_logger
from app.scrapers.base import BaseScraper

logger = get_logger(__name__)


class ScraperRegistry:
    """
    Central registry managing all available content scrapers.

    Supports both manual registration and auto-discovery of
    scraper implementations from the app.scrapers package.
    """

    def __init__(self):
        self._scrapers: Dict[str, BaseScraper] = {}

    def register(self, scraper: BaseScraper) -> None:
        """
        Register a scraper instance in the registry.

        Args:
            scraper: An instance of a BaseScraper implementation.

        Raises:
            ValueError: If a scraper with the same source name is already registered.
        """
        name = scraper.get_source_name()
        if name in self._scrapers:
            raise ValueError(
                f"Scraper '{name}' is already registered. "
                f"Use deregister() first to replace it."
            )
        self._scrapers[name] = scraper
        logger.info(f"Registered scraper: {scraper.get_source_display_name()} ({name})")

    def deregister(self, source_name: str) -> Optional[BaseScraper]:
        """
        Remove a scraper from the registry.

        Args:
            source_name: The source name identifier to remove.

        Returns:
            The removed scraper instance, or None if not found.
        """
        scraper = self._scrapers.pop(source_name, None)
        if scraper:
            logger.info(f"Deregistered scraper: {source_name}")
        return scraper

    def get(self, source_name: str) -> Optional[BaseScraper]:
        """Get a specific scraper by source name."""
        return self._scrapers.get(source_name)

    def get_all(self) -> List[BaseScraper]:
        """Get all registered scrapers."""
        return list(self._scrapers.values())

    def get_names(self) -> List[str]:
        """Get all registered source names."""
        return list(self._scrapers.keys())

    def get_source_info(self) -> List[dict]:
        """Get metadata for all registered sources (for API/UI)."""
        return [scraper.get_source_info() for scraper in self._scrapers.values()]

    def auto_discover(self) -> None:
        """
        Auto-discover and register all built-in scrapers.

        Imports all known scraper modules and registers their instances.
        New scrapers added to the package will be picked up automatically
        when added to the import list below.
        """
        from app.scrapers.youtube_scraper import YouTubeChannelScraper
        from app.scrapers.openai_scraper import OpenAIBlogScraper
        from app.scrapers.anthropic_scraper import AnthropicBlogScraper
        from app.scrapers.arxiv_scraper import ArxivScraper
        from app.scrapers.deepmind_scraper import DeepMindScraper
        from app.scrapers.huggingface_scraper import HuggingFaceScraper

        default_scrapers: List[BaseScraper] = [
            YouTubeChannelScraper(),
            OpenAIBlogScraper(),
            AnthropicBlogScraper(),
            ArxivScraper(),
            DeepMindScraper(),
            HuggingFaceScraper(),
        ]

        for scraper in default_scrapers:
            try:
                self.register(scraper)
            except Exception as e:
                logger.warning(f"Failed to register {scraper.__class__.__name__}: {e}")

        logger.info(
            f"Auto-discovery complete: {len(self._scrapers)} scrapers registered"
        )

    def __len__(self) -> int:
        return len(self._scrapers)

    def __contains__(self, source_name: str) -> bool:
        return source_name in self._scrapers
