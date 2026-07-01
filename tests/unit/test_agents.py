from unittest.mock import patch, MagicMock
from app.agent.digest_agent import DigestAgent, DigestOutput
from app.agent.curator_agent import CuratorAgent, RankedArticle, RankedDigestList
from app.agent.email_agent import EmailAgent, EmailIntroduction, RankedArticleDetail


class TestDigestAgent:
    @patch("app.agent.base.OpenAI")
    def test_generate_digest_success(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = DigestOutput(
            title="Test Title Summarized",
            summary="This is a summary of the test article.",
        )
        mock_client.responses.parse.return_value = mock_response

        agent = DigestAgent()
        result = agent.generate_digest(
            title="Raw Title",
            content="Raw content text...",
            article_type="openai",
        )

        assert result is not None
        assert result.title == "Test Title Summarized"
        assert result.summary == "This is a summary of the test article."

    @patch("app.agent.base.OpenAI")
    def test_generate_digest_handles_api_error(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.responses.parse.side_effect = Exception("OpenAI API error")

        agent = DigestAgent()
        result = agent.generate_digest(
            title="Raw Title",
            content="Raw content text...",
            article_type="openai",
        )

        assert result is None


class TestCuratorAgent:
    @patch("app.agent.base.OpenAI")
    def test_rank_digests_success(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = RankedDigestList(
            articles=[
                RankedArticle(
                    digest_id="youtube:123",
                    relevance_score=8.5,
                    rank=1,
                    reasoning="High technical relevance.",
                )
            ]
        )
        mock_client.responses.parse.return_value = mock_response

        user_profile = {
            "name": "Dave",
            "background": "AI Engineer",
            "interests": ["LLMs"],
            "preferences": {"prefer_practical": True},
            "expertise_level": "Advanced",
        }
        agent = CuratorAgent(user_profile=user_profile)
        ranked = agent.rank_digests(
            [
                {
                    "id": "youtube:123",
                    "title": "Title 1",
                    "summary": "Summary 1",
                    "article_type": "youtube",
                }
            ]
        )

        assert len(ranked) == 1
        assert ranked[0].digest_id == "youtube:123"
        assert ranked[0].relevance_score == 8.5


class TestEmailAgent:
    @patch("app.agent.base.OpenAI")
    def test_generate_introduction(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = EmailIntroduction(
            greeting="Hey Dave, here is your daily news for July 01, 2026.",
            introduction="Here are the top ranked AI news articles.",
        )
        mock_client.responses.parse.return_value = mock_response

        user_profile = {
            "name": "Dave",
            "background": "AI Engineer",
            "interests": ["LLMs"],
            "preferences": {"prefer_practical": True},
            "expertise_level": "Advanced",
        }
        agent = EmailAgent(user_profile=user_profile)

        ranked_details = [
            RankedArticleDetail(
                digest_id="youtube:123",
                rank=1,
                relevance_score=8.5,
                title="Title 1",
                summary="Summary 1",
                url="https://youtube.com/watch?v=123",
                article_type="youtube",
            )
        ]
        intro = agent.generate_introduction(ranked_details)
        assert intro.greeting.startswith("Hey Dave")
        assert intro.introduction == "Here are the top ranked AI news articles."

        # Test markdown response wrapper
        response = agent.create_email_digest_response(ranked_details, total_ranked=1)
        markdown = response.to_markdown()
        assert "## Title 1" in markdown
        assert "[Read more →]" in markdown
