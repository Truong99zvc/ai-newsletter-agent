"""
Hugging Face blog scraper plugin.

Scrapes articles from the Hugging Face blog RSS feed,
covering model releases, research highlights, and tutorials.
"""

from datetime import datetime, timedelta, timezone
from typing import List

import feedparser
from docling.document_converter import DocumentConverter

from app.logging_config import get_logger
from app.scrapers.base import BaseScraper, ScrapedItem

logger = get_logger(__name__)


class HuggingFaceScraper(BaseScraper):
    """
    Scrapes the latest articles from the Hugging Face blog.

    Covers model releases, research highlights, tutorials, and
    community updates from the HF ecosystem.
    """

    RSS_URL = "https://huggingface.co/blog/feed.xml"

    def __init__(self):
        self.converter = DocumentConverter()

    def get_source_name(self) -> str:
        return "huggingface"

    def get_source_display_name(self) -> str:
        return "Hugging Face"

    def scrape(self, hours: int = 24) -> List[ScrapedItem]:
        """Scrape recent articles from Hugging Face's RSS feed."""
        items = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            feed = feedparser.parse(self.RSS_URL)
            if not feed.entries:
                logger.debug("No entries found in HuggingFace RSS feed")
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

                    guid = entry.get("id", entry.get("link", ""))

                    items.append(ScrapedItem(
                        source_id=guid,
                        source_type=self.get_source_name(),
                        title=entry.get("title", ""),
                        url=entry.get("link", ""),
                        description=entry.get("description", entry.get("summary", "")),
                        published_at=published_time,
                        category=category,
                    ))
        except Exception as e:
            logger.error(f"Error scraping HuggingFace RSS: {e}")

        logger.info(f"Scraped {len(items)} articles from Hugging Face")
        return items

    def enrich(self, item: ScrapedItem) -> ScrapedItem:
        """Fetch full article content as Markdown using Docling."""
        try:
            result = self.converter.convert(item.url)
            markdown = result.document.export_to_markdown()
            if markdown:
                return item.model_copy(update={"content": markdown})
        except Exception as e:
            logger.warning(f"Failed to enrich HuggingFace article {item.url}: {e}")
        return item
