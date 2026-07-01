from datetime import datetime, timezone


def test_create_youtube_video(repository, sample_youtube_video):
    video = repository.create_youtube_video(**sample_youtube_video)
    assert video is not None
    assert video.video_id == sample_youtube_video["video_id"]
    assert video.title == sample_youtube_video["title"]

    # Trying to create the same video again should return None (duplicate check)
    duplicate = repository.create_youtube_video(**sample_youtube_video)
    assert duplicate is None


def test_bulk_create_youtube_videos(repository, sample_youtube_video):
    videos = [
        sample_youtube_video,
        {
            "video_id": "test_video_456",
            "title": "Second Video",
            "url": "https://youtube.com/watch?v=test_video_456",
            "channel_id": "UCtest123",
            "published_at": datetime.now(timezone.utc),
            "description": "Desc",
            "transcript": None,
        },
    ]

    count = repository.bulk_create_youtube_videos(videos)
    assert count == 2

    # Verify that get_youtube_videos_without_transcript returns the video with transcript=None
    without_transcript = repository.get_youtube_videos_without_transcript()
    assert len(without_transcript) == 1
    assert without_transcript[0].video_id == "test_video_456"

    # Update transcript and verify
    success = repository.update_youtube_video_transcript(
        "test_video_456", "Updated transcript text"
    )
    assert success is True
    assert len(repository.get_youtube_videos_without_transcript()) == 0


def test_create_openai_article(repository, sample_openai_article):
    article = repository.create_openai_article(**sample_openai_article)
    assert article is not None
    assert article.guid == sample_openai_article["guid"]

    duplicate = repository.create_openai_article(**sample_openai_article)
    assert duplicate is None


def test_bulk_create_openai_articles(repository, sample_openai_article):
    articles = [
        sample_openai_article,
        {
            "guid": "openai-article-2",
            "title": "Another release",
            "url": "https://openai.com/news/article-2",
            "published_at": datetime.now(timezone.utc),
            "description": "Desc",
            "category": "safety",
        },
    ]

    count = repository.bulk_create_openai_articles(articles)
    assert count == 2


def test_create_anthropic_article(repository, sample_anthropic_article):
    article = repository.create_anthropic_article(**sample_anthropic_article)
    assert article is not None
    assert article.guid == sample_anthropic_article["guid"]

    duplicate = repository.create_anthropic_article(**sample_anthropic_article)
    assert duplicate is None


def test_bulk_create_anthropic_articles(repository, sample_anthropic_article):
    articles = [
        sample_anthropic_article,
        {
            "guid": "anthropic-article-2",
            "title": "Claude 3.5 Sonnet",
            "url": "https://anthropic.com/news/article-2",
            "published_at": datetime.now(timezone.utc),
            "description": "Desc",
            "category": "releases",
        },
    ]

    count = repository.bulk_create_anthropic_articles(articles)
    assert count == 2

    without_markdown = repository.get_anthropic_articles_without_markdown()
    assert len(without_markdown) == 2

    # Update markdown and verify
    success = repository.update_anthropic_article_markdown(
        "anthropic-article-2", "# Claude 3.5 Sonnet Details"
    )
    assert success is True
    assert len(repository.get_anthropic_articles_without_markdown()) == 1


def test_digests_creation_and_retrieval(
    repository, sample_youtube_video, sample_openai_article
):
    # Setup: Create raw articles/videos
    repository.create_youtube_video(**sample_youtube_video)
    repository.create_openai_article(**sample_openai_article)

    # Initially, we have articles without digest
    articles_no_digest = repository.get_articles_without_digest()
    assert len(articles_no_digest) == 2

    # Create a digest for the YouTube video
    digest = repository.create_digest(
        article_type="youtube",
        article_id=sample_youtube_video["video_id"],
        url=sample_youtube_video["url"],
        title="Mock Video Digest",
        summary="A mock digest summary.",
        published_at=sample_youtube_video["published_at"],
    )
    assert digest is not None
    assert digest.title == "Mock Video Digest"

    # Now only the OpenAI article should be without digest
    remaining = repository.get_articles_without_digest()
    assert len(remaining) == 1
    assert remaining[0]["id"] == sample_openai_article["guid"]

    # Verify retrieval of recent digests
    recent = repository.get_recent_digests(hours=24)
    assert len(recent) == 1
    assert recent[0]["title"] == "Mock Video Digest"
    assert recent[0]["sent_at"] is None

    # Mark as sent
    repository.mark_digests_as_sent([digest.id])

    # Verify sent_at is updated
    updated_recent = repository.get_recent_digests(hours=24, exclude_sent=False)
    assert len(updated_recent) == 1
    assert updated_recent[0]["sent_at"] is not None
