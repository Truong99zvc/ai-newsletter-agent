"""
OpenAI blog scraper plugin.

Scrapes articles from the OpenAI news RSS feed.
"""

from datetime import datetime, timedelta, timezone
from typing import List

import feedparser

from app.logging_config import get_logger
from app.scrapers.base import BaseScraper, ScrapedItem

logger = get_logger(__name__)


class OpenAIBlogScraper(BaseScraper):
    """
    Scrapes the latest articles from the OpenAI blog via RSS.
    """

    RSS_URL = "https://openai.com/news/rss.xml"

    def get_source_name(self) -> str:
        return "openai"

    def get_source_display_name(self) -> str:
        return "OpenAI Blog"

    def scrape(self, hours: int = 24) -> List[ScrapedItem]:
        """Scrape recent articles from OpenAI's RSS feed."""
        items = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            feed = feedparser.parse(self.RSS_URL)
            if not feed.entries:
                logger.debug("No entries found in OpenAI RSS feed")
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

                    items.append(ScrapedItem(
                        source_id=entry.get("id", entry.get("link", "")),
                        source_type=self.get_source_name(),
                        title=entry.get("title", ""),
                        url=entry.get("link", ""),
                        description=entry.get("description", ""),
                        published_at=published_time,
                        category=category,
                    ))
        except Exception as e:
            logger.error(f"Error scraping OpenAI RSS: {e}")

        logger.info(f"Scraped {len(items)} articles from OpenAI")
        return items
