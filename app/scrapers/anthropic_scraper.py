"""
Anthropic blog scraper plugin.

Scrapes articles from Anthropic's news, research, and engineering feeds.
Uses Docling for full article content extraction.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import feedparser
from docling.document_converter import DocumentConverter

from app.logging_config import get_logger
from app.scrapers.base import BaseScraper, ScrapedItem

logger = get_logger(__name__)


class AnthropicBlogScraper(BaseScraper):
    """
    Scrapes articles from Anthropic's three blog feeds:
    - News
    - Research
    - Engineering

    Deduplicates by GUID across feeds. Uses Docling to convert
    full article pages to Markdown during enrichment.
    """

    RSS_URLS = [
        "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
        "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
        "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
    ]

    def __init__(self):
        self.converter = DocumentConverter()

    def get_source_name(self) -> str:
        return "anthropic"

    def get_source_display_name(self) -> str:
        return "Anthropic Blog"

    def scrape(self, hours: int = 24) -> List[ScrapedItem]:
        """Scrape recent articles from all Anthropic RSS feeds with deduplication."""
        items = []
        seen_guids = set()
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        for rss_url in self.RSS_URLS:
            try:
                feed = feedparser.parse(rss_url)
                if not feed.entries:
                    continue

                for entry in feed.entries:
                    published_parsed = getattr(entry, "published_parsed", None)
                    if not published_parsed:
                        continue

                    published_time = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                    if published_time >= cutoff_time:
                        guid = entry.get("id", entry.get("link", ""))
                        if guid not in seen_guids:
                            seen_guids.add(guid)

                            category = None
                            if entry.get("tags"):
                                category = entry["tags"][0].get("term")

                            items.append(ScrapedItem(
                                source_id=guid,
                                source_type=self.get_source_name(),
                                title=entry.get("title", ""),
                                url=entry.get("link", ""),
                                description=entry.get("description", ""),
                                published_at=published_time,
                                category=category,
                            ))
            except Exception as e:
                logger.error(f"Error scraping Anthropic feed {rss_url}: {e}")

        logger.info(f"Scraped {len(items)} articles from Anthropic ({len(self.RSS_URLS)} feeds)")
        return items

    def enrich(self, item: ScrapedItem) -> ScrapedItem:
        """Fetch full article content as Markdown using Docling."""
        try:
            result = self.converter.convert(item.url)
            markdown = result.document.export_to_markdown()
            if markdown:
                return item.model_copy(update={"content": markdown})
        except Exception as e:
            logger.warning(f"Failed to convert {item.url} to markdown: {e}")
        return item
