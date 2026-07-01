from unittest.mock import patch, MagicMock
import pytest

from app.scrapers.openai import OpenAIScraper
from app.scrapers.anthropic import AnthropicScraper
from app.scrapers.youtube import YouTubeScraper


class FeedEntry:
    """Helper mock class representing a feed entry that supports both dict .get() and attribute access."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)


@pytest.fixture
def mock_rss_feed():
    feed = MagicMock()
    entry = FeedEntry(
        title="Test Article Title",
        description="Test Description",
        link="https://example.com/article-1",
        id="guid-123",
        published_parsed=(2026, 6, 30, 12, 0, 0, 0, 0, 0),
        tags=[{"term": "tech"}],
    )
    feed.entries = [entry]
    return feed


@patch("app.scrapers.base.feedparser.parse")
def test_openai_scraper(mock_parse, mock_rss_feed):
    mock_parse.return_value = mock_rss_feed
    scraper = OpenAIScraper()
    articles = scraper.get_articles(hours=48)

    assert len(articles) == 1
    assert articles[0].title == "Test Article Title"
    assert articles[0].guid == "guid-123"
    assert articles[0].url == "https://example.com/article-1"


@patch("app.scrapers.base.feedparser.parse")
def test_anthropic_scraper(mock_parse, mock_rss_feed):
    mock_parse.return_value = mock_rss_feed
    scraper = AnthropicScraper()
    articles = scraper.get_articles(hours=48)

    # Anthropic has 3 feeds, so if mock_parse returns the same feed 3 times, we expect deduplication
    assert len(articles) == 1
    assert articles[0].title == "Test Article Title"
    assert articles[0].guid == "guid-123"


class TestYouTubeScraper:
    @patch("app.scrapers.youtube.feedparser.parse")
    def test_get_latest_videos(self, mock_parse):
        feed = MagicMock()
        entry = FeedEntry(
            title="Test Video Title",
            link="https://www.youtube.com/watch?v=abc123xyz",
            published_parsed=(2026, 6, 30, 12, 0, 0, 0, 0, 0),
            summary="Video Summary",
        )
        feed.entries = [entry]
        mock_parse.return_value = feed

        scraper = YouTubeScraper()
        videos = scraper.get_latest_videos(channel_id="UCtest", hours=48)

        assert len(videos) == 1
        assert videos[0].title == "Test Video Title"
        assert videos[0].video_id == "abc123xyz"

    @patch("app.scrapers.youtube.YouTubeTranscriptApi")
    def test_get_transcript(self, mock_transcript_api_cls):
        mock_api = MagicMock()
        mock_transcript_api_cls.return_value = mock_api

        # Mock returned transcript object
        mock_snippet = MagicMock()
        mock_snippet.text = "Hello world transcript snippet"
        mock_transcript = MagicMock()
        mock_transcript.snippets = [mock_snippet]
        mock_api.fetch.return_value = mock_transcript

        scraper = YouTubeScraper()
        transcript = scraper.get_transcript(video_id="abc123xyz")
        assert transcript is not None
        assert transcript.text == "Hello world transcript snippet"
