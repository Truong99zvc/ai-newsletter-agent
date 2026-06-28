"""
Google DeepMind blog scraper plugin.

Scrapes articles from the Google DeepMind blog RSS feed.
"""

from datetime import datetime, timedelta, timezone
from typing import List

import feedparser
from docling.document_converter import DocumentConverter

from app.logging_config import get_logger
from app.scrapers.base import BaseScraper, ScrapedItem

logger = get_logger(__name__)


class DeepMindScraper(BaseScraper):
    """
    Scrapes the latest articles from the Google DeepMind blog.

    Uses the DeepMind RSS feed for discovery and Docling for
    full article content extraction during enrichment.
    """

    RSS_URL = "https://deepmind.google/blog/rss.xml"

    def __init__(self):
        self.converter = DocumentConverter()

    def get_source_name(self) -> str:
        return "deepmind"

    def get_source_display_name(self) -> str:
        return "Google DeepMind"

    def scrape(self, hours: int = 24) -> List[ScrapedItem]:
        """Scrape recent articles from Google DeepMind's RSS feed."""
        items = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            feed = feedparser.parse(self.RSS_URL)
            if not feed.entries:
                logger.debug("No entries found in DeepMind RSS feed")
                return []

            for entry in feed.entries:
                published_parsed = getattr(entry, "published_parsed", None)
                if not published_parsed:
                    continue

                published_time = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                if published_time >= cutoff_time:
                    category = None
                    if entry.get("tags"):
                        category = entry["tags"][0].get("term")

                    items.append(
                        ScrapedItem(
                            source_id=entry.get("id", entry.get("link", "")),
                            source_type=self.get_source_name(),
                            title=entry.get("title", ""),
                            url=entry.get("link", ""),
                            description=entry.get(
                                "description", entry.get("summary", "")
                            ),
                            published_at=published_time,
                            category=category,
                        )
                    )
        except Exception as e:
            logger.error(f"Error scraping DeepMind RSS: {e}")

        logger.info(f"Scraped {len(items)} articles from Google DeepMind")
        return items

    def enrich(self, item: ScrapedItem) -> ScrapedItem:
        """Fetch full article content as Markdown using Docling."""
        try:
            result = self.converter.convert(item.url)
            markdown = result.document.export_to_markdown()
            if markdown:
                return item.model_copy(update={"content": markdown})
        except Exception as e:
            logger.warning(f"Failed to enrich DeepMind article {item.url}: {e}")
        return item
