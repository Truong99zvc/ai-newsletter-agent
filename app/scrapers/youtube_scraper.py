"""
YouTube channel scraper plugin.

Scrapes videos from configured YouTube channels via RSS feeds
and fetches video transcripts using the youtube-transcript-api.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.proxies import WebshareProxyConfig

from app.logging_config import get_logger
from app.scrapers.base import BaseScraper, ScrapedItem
from app.settings import get_settings

logger = get_logger(__name__)


class YouTubeChannelScraper(BaseScraper):
    """
    Scrapes latest videos from configured YouTube channels.

    Uses YouTube RSS feeds for discovery and youtube-transcript-api
    for transcript extraction. Supports optional proxy configuration
    for transcript fetching.
    """

    def __init__(self, channel_ids: Optional[List[str]] = None):
        settings = get_settings()
        proxy_config = None

        if settings.proxy.is_configured:
            proxy_config = WebshareProxyConfig(
                proxy_username=settings.proxy.username,
                proxy_password=settings.proxy.password,
            )

        self.transcript_api = YouTubeTranscriptApi(proxy_config=proxy_config)

        # Use provided channels or fall back to config
        if channel_ids:
            self.channel_ids = channel_ids
        else:
            from app.config import YOUTUBE_CHANNELS

            self.channel_ids = YOUTUBE_CHANNELS

    def get_source_name(self) -> str:
        return "youtube"

    def get_source_display_name(self) -> str:
        return "YouTube"

    def _get_rss_url(self, channel_id: str) -> str:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    def _extract_video_id(self, video_url: str) -> str:
        if "youtube.com/watch?v=" in video_url:
            return video_url.split("v=")[1].split("&")[0]
        if "youtube.com/shorts/" in video_url:
            return video_url.split("shorts/")[1].split("?")[0]
        if "youtu.be/" in video_url:
            return video_url.split("youtu.be/")[1].split("?")[0]
        return video_url

    def scrape(self, hours: int = 24) -> List[ScrapedItem]:
        """Scrape recent videos from all configured YouTube channels."""
        items = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        for channel_id in self.channel_ids:
            try:
                feed = feedparser.parse(self._get_rss_url(channel_id))
                if not feed.entries:
                    logger.debug(f"No entries found for channel {channel_id}")
                    continue

                for entry in feed.entries:
                    # Skip YouTube Shorts
                    if "/shorts/" in entry.link:
                        continue

                    published_time = datetime(
                        *entry.published_parsed[:6], tzinfo=timezone.utc
                    )
                    if published_time >= cutoff_time:
                        video_id = self._extract_video_id(entry.link)
                        items.append(
                            ScrapedItem(
                                source_id=video_id,
                                source_type=self.get_source_name(),
                                title=entry.title,
                                url=entry.link,
                                description=entry.get("summary", ""),
                                published_at=published_time,
                                metadata={"channel_id": channel_id},
                            )
                        )
            except Exception as e:
                logger.error(f"Error scraping channel {channel_id}: {e}")

        logger.info(
            f"Scraped {len(items)} videos from {len(self.channel_ids)} channels"
        )
        return items

    def enrich(self, item: ScrapedItem) -> ScrapedItem:
        """Fetch transcript for a YouTube video."""
        try:
            transcript = self.transcript_api.fetch(item.source_id)
            text = " ".join([snippet.text for snippet in transcript.snippets])
            return item.model_copy(update={"content": text})
        except (TranscriptsDisabled, NoTranscriptFound):
            logger.debug(f"No transcript available for {item.source_id}")
            return item.model_copy(update={"content": "__UNAVAILABLE__"})
        except Exception as e:
            logger.warning(f"Error fetching transcript for {item.source_id}: {e}")
            return item.model_copy(update={"content": "__UNAVAILABLE__"})

    def get_source_info(self) -> dict:
        info = super().get_source_info()
        info["channel_count"] = len(self.channel_ids)
        info["channel_ids"] = self.channel_ids
        return info
