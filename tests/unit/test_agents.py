"""
Unit tests for AI agent modules.

Tests digest generation, curation ranking, and email composition
using mocked OpenAI API responses.
"""

from unittest.mock import patch, MagicMock

import pytest

from app.agent.digest_agent import DigestAgent, DigestOutput
from app.agent.curator_agent import CuratorAgent, RankedArticle, RankedDigestList


class TestDigestAgent:
    """Tests for the DigestAgent."""

    @patch("app.agent.digest_agent.OpenAI")
    def test_generate_digest_success(self, mock_openai_cls):
        """Should generate a digest with title and summary."""
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = DigestOutput(
            title="GPT-5 Brings Major Reasoning Improvements",
            summary="OpenAI releases GPT-5 with significant advances in multi-step reasoning.",
        )
        mock_client.responses.parse.return_value = mock_response

        agent = DigestAgent()
        result = agent.generate_digest(
            title="Introducing GPT-5",
            content="OpenAI has released GPT-5, their latest model...",
            article_type="openai",
        )

        assert result is not None
        assert result.title == "GPT-5 Brings Major Reasoning Improvements"
        assert "reasoning" in result.summary.lower()

    @patch("app.agent.digest_agent.OpenAI")
    def test_generate_digest_handles_api_error(self, mock_openai_cls):
        """Should return None when the API call fails."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.responses.parse.side_effect = Exception("API Error")

        agent = DigestAgent()
        result = agent.generate_digest(
            title="Test", content="Content", article_type="openai",
        )
        assert result is None

    def test_digest_output_model(self):
        """Should validate DigestOutput schema."""
        output = DigestOutput(
            title="Test Title",
            summary="Test summary for the article.",
        )
        assert output.title == "Test Title"
        assert output.summary == "Test summary for the article."


class TestCuratorAgent:
    """Tests for the CuratorAgent."""

    @patch("app.agent.curator_agent.OpenAI")
    def test_rank_digests_success(self, mock_openai_cls):
        """Should rank a list of digests."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = RankedDigestList(
            articles=[
                RankedArticle(
                    digest_id="openai:001", relevance_score=9.2,
                    rank=1, reasoning="Highly relevant to user interests",
                ),
                RankedArticle(
                    digest_id="arxiv:002", relevance_score=7.5,
                    rank=2, reasoning="Good technical depth",
                ),
            ]
        )
        mock_client.responses.parse.return_value = mock_response

        user_profile = {
            "name": "Test User",
            "background": "AI Engineer",
            "interests": ["LLMs", "AI Safety"],
            "preferences": {"prefer_practical": True},
            "expertise_level": "Advanced",
        }
        agent = CuratorAgent(user_profile)
        result = agent.rank_digests([
            {"id": "openai:001", "title": "GPT-5", "summary": "New model", "article_type": "openai"},
            {"id": "arxiv:002", "title": "Safety Paper", "summary": "New research", "article_type": "arxiv"},
        ])

        assert len(result) == 2
        assert result[0].rank == 1
        assert result[0].relevance_score == 9.2

    @patch("app.agent.curator_agent.OpenAI")
    def test_rank_empty_list(self, mock_openai_cls):
        """Should return empty list for no digests."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        user_profile = {
            "name": "Test",
            "background": "Engineer",
            "interests": ["AI"],
            "preferences": {},
            "expertise_level": "Beginner",
        }
        agent = CuratorAgent(user_profile)
        result = agent.rank_digests([])
        assert result == []

    def test_ranked_article_model(self):
        """Should validate RankedArticle schema."""
        article = RankedArticle(
            digest_id="test:001",
            relevance_score=8.0,
            rank=1,
            reasoning="Very relevant",
        )
        assert article.relevance_score >= 0
        assert article.relevance_score <= 10
        assert article.rank >= 1

    def test_ranked_article_score_bounds(self):
        """Should reject scores outside 0-10 range."""
        with pytest.raises(Exception):
            RankedArticle(
                digest_id="test:001",
                relevance_score=15.0,  # Invalid
                rank=1,
                reasoning="Test",
            )
