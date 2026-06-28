"""
arXiv papers scraper plugin.

Scrapes recent AI/ML papers from arXiv using their Atom feed API.
Filters papers by relevant AI categories (cs.AI, cs.LG, cs.CL, cs.CV, stat.ML).
"""

from datetime import datetime, timedelta, timezone
from typing import List
from xml.etree import ElementTree

import requests

from app.logging_config import get_logger
from app.scrapers.base import BaseScraper, ScrapedItem

logger = get_logger(__name__)

# arXiv categories relevant to AI/ML
ARXIV_CATEGORIES = [
    "cs.AI",  # Artificial Intelligence
    "cs.LG",  # Machine Learning
    "cs.CL",  # Computation and Language (NLP)
    "cs.CV",  # Computer Vision
    "stat.ML",  # Machine Learning (Statistics)
]

ARXIV_API_URL = "http://export.arxiv.org/api/query"


class ArxivScraper(BaseScraper):
    """
    Scrapes recent AI/ML papers from arXiv.

    Uses the arXiv API to search for papers in relevant categories,
    returning titles, abstracts, and author information.
    """

    def __init__(self, categories: List[str] = None, max_results: int = 30):
        self.categories = categories or ARXIV_CATEGORIES
        self.max_results = max_results

    def get_source_name(self) -> str:
        return "arxiv"

    def get_source_display_name(self) -> str:
        return "arXiv Papers"

    def _build_query(self) -> str:
        """Build arXiv API search query for relevant categories."""
        cat_queries = [f"cat:{cat}" for cat in self.categories]
        return " OR ".join(cat_queries)

    def scrape(self, hours: int = 24) -> List[ScrapedItem]:
        """Scrape recent papers from arXiv in AI/ML categories."""
        items = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            params = {
                "search_query": self._build_query(),
                "start": 0,
                "max_results": self.max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }

            response = requests.get(ARXIV_API_URL, params=params, timeout=30)
            response.raise_for_status()

            # Parse Atom XML feed
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom",
            }
            root = ElementTree.fromstring(response.text)

            for entry in root.findall("atom:entry", ns):
                # Parse published date
                published_str = entry.find("atom:published", ns)
                if published_str is None or published_str.text is None:
                    continue

                published_time = datetime.fromisoformat(
                    published_str.text.replace("Z", "+00:00")
                )

                if published_time < cutoff_time:
                    continue

                # Extract paper ID from the URL
                paper_id_elem = entry.find("atom:id", ns)
                paper_id = paper_id_elem.text if paper_id_elem is not None else ""
                paper_id_short = (
                    paper_id.split("/abs/")[-1] if "/abs/" in paper_id else paper_id
                )

                title_elem = entry.find("atom:title", ns)
                title = (
                    title_elem.text.strip().replace("\n", " ")
                    if title_elem is not None
                    else ""
                )

                summary_elem = entry.find("atom:summary", ns)
                summary = (
                    summary_elem.text.strip().replace("\n", " ")
                    if summary_elem is not None
                    else ""
                )

                # Get PDF link
                pdf_url = paper_id.replace("/abs/", "/pdf/") if paper_id else ""

                # Get authors
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)

                # Get categories
                categories = []
                for cat in entry.findall("atom:category", ns):
                    term = cat.get("term", "")
                    if term:
                        categories.append(term)

                primary_category = categories[0] if categories else None

                items.append(
                    ScrapedItem(
                        source_id=paper_id_short,
                        source_type=self.get_source_name(),
                        title=title,
                        url=paper_id,
                        description=summary,
                        content=summary,  # Abstract as initial content
                        published_at=published_time,
                        category=primary_category,
                        metadata={
                            "authors": authors,
                            "categories": categories,
                            "pdf_url": pdf_url,
                        },
                    )
                )

        except Exception as e:
            logger.error(f"Error scraping arXiv: {e}")

        logger.info(f"Scraped {len(items)} papers from arXiv")
        return items

    def get_source_info(self) -> dict:
        info = super().get_source_info()
        info["categories"] = self.categories
        info["max_results"] = self.max_results
        return info
