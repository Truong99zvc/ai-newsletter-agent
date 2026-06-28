"""
Pipeline orchestrator for the AI Newsletter Agent.

Manages the multi-step pipeline execution with:
- State tracking per step (PENDING → RUNNING → SUCCESS/FAILED)
- Concurrent scraping across sources
- Retry logic with exponential backoff
- Pipeline run persistence for monitoring/API
- Graceful error handling with step-level isolation

Pipeline Steps:
1. SCRAPE   — Fetch new content from all registered sources
2. ENRICH   — Fill in full content (transcripts, markdown)
3. DIGEST   — Generate AI summaries for new content
4. CURATE   — Rank digests by user relevance
5. DELIVER  — Compose and send email newsletter
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.logging_config import get_logger
from app.settings import get_settings
from app.scrapers.base import ScrapedItem
from app.scrapers.registry import ScraperRegistry
from app.database.repository import Repository
from app.agent.digest_agent import DigestAgent
from app.agent.curator_agent import CuratorAgent
from app.agent.email_agent import EmailAgent, RankedArticleDetail
from app.profiles.user_profile import USER_PROFILE
from app.services.email import send_email, digest_to_html

logger = get_logger(__name__)

# Pipeline step identifiers
STEP_SCRAPE = "scrape"
STEP_ENRICH = "enrich"
STEP_DIGEST = "digest"
STEP_CURATE = "curate"
STEP_DELIVER = "deliver"

ALL_STEPS = [STEP_SCRAPE, STEP_ENRICH, STEP_DIGEST, STEP_CURATE, STEP_DELIVER]


class PipelineOrchestrator:
    """
    Orchestrates the full AI newsletter pipeline.

    Manages state transitions, error handling, and persistence
    for each pipeline execution run.
    """

    def __init__(
        self,
        registry: Optional[ScraperRegistry] = None,
        repo: Optional[Repository] = None,
    ):
        self.settings = get_settings()
        self.repo = repo or Repository()
        self.registry = registry or self._default_registry()
        self._executor = ThreadPoolExecutor(
            max_workers=self.settings.pipeline.max_concurrent_scrapers
        )

    def _default_registry(self) -> ScraperRegistry:
        """Create and populate the default scraper registry."""
        registry = ScraperRegistry()
        registry.auto_discover()
        return registry

    def run(self, hours: int = 24, top_n: int = 10, send_email_flag: bool = True) -> Dict[str, Any]:
        """
        Execute the full pipeline synchronously.

        Args:
            hours: Lookback window in hours for scraping.
            top_n: Number of top articles to include in email.
            send_email_flag: Whether to send the email at the end.

        Returns:
            Dict with run results including status, counts, and timing.
        """
        # Create pipeline run record
        run = self.repo.create_pipeline_run(hours=hours, top_n=top_n)
        run_id = run.id
        self.repo.update_pipeline_run(run_id, status="running")

        results: Dict[str, Any] = {
            "run_id": run_id,
            "status": "running",
            "steps": {},
            "start_time": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Step 1: Scrape
            scrape_result = self._step_scrape(run_id, hours)
            results["steps"][STEP_SCRAPE] = scrape_result

            # Step 2: Enrich
            enrich_result = self._step_enrich(run_id)
            results["steps"][STEP_ENRICH] = enrich_result

            # Step 3: Digest
            digest_result = self._step_digest(run_id)
            results["steps"][STEP_DIGEST] = digest_result

            # Step 4: Curate
            curate_result = self._step_curate(run_id, hours)
            results["steps"][STEP_CURATE] = curate_result

            # Step 5: Deliver
            if send_email_flag:
                deliver_result = self._step_deliver(run_id, hours, top_n)
                results["steps"][STEP_DELIVER] = deliver_result
            else:
                results["steps"][STEP_DELIVER] = {"status": "skipped"}
                self.repo.update_pipeline_run(run_id, email_sent="skipped")

            # Mark success
            completed_at = datetime.now(timezone.utc)
            started_at = run.started_at
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            duration = (completed_at - started_at).total_seconds()

            self.repo.update_pipeline_run(
                run_id,
                status="success",
                completed_at=completed_at,
                duration_seconds=duration,
                steps_completed={step: results["steps"][step].get("status", "unknown") for step in ALL_STEPS},
            )
            results["status"] = "success"
            results["duration_seconds"] = duration

            logger.info(f"Pipeline run {run_id} completed successfully in {duration:.1f}s")

        except Exception as e:
            logger.error(f"Pipeline run {run_id} failed: {e}", exc_info=True)
            self.repo.update_pipeline_run(
                run_id,
                status="failed",
                completed_at=datetime.now(timezone.utc),
                error_message=str(e),
            )
            results["status"] = "failed"
            results["error"] = str(e)

        return results

    # ──────────────────────────────────────────────
    # Pipeline Steps
    # ──────────────────────────────────────────────

    def _step_scrape(self, run_id: str, hours: int) -> Dict[str, Any]:
        """Step 1: Scrape all sources concurrently."""
        logger.info(f"[1/5] Scraping content from {len(self.registry)} sources...")
        self.repo.update_pipeline_run(run_id, current_step=STEP_SCRAPE)

        all_items: List[ScrapedItem] = []
        source_counts: Dict[str, int] = {}

        # Run scrapers concurrently using thread pool
        scrapers = self.registry.get_all()
        futures = {}
        for scraper in scrapers:
            future = self._executor.submit(self._scrape_source, scraper, hours)
            futures[scraper.get_source_name()] = future

        for source_name, future in futures.items():
            try:
                items = future.result(timeout=120)
                all_items.extend(items)
                source_counts[source_name] = len(items)
                logger.info(f"  ✓ {source_name}: {len(items)} items")
            except Exception as e:
                logger.error(f"  ✗ {source_name}: {e}")
                source_counts[source_name] = 0

        # Store all items
        stored = self.repo.bulk_upsert_scraped_content([
            item.model_dump() for item in all_items
        ])

        self.repo.update_pipeline_run(run_id, articles_scraped=stored)
        logger.info(f"  Total: {len(all_items)} scraped, {stored} new")

        return {
            "status": "success",
            "total_scraped": len(all_items),
            "new_stored": stored,
            "by_source": source_counts,
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def _scrape_source(self, scraper, hours: int) -> List[ScrapedItem]:
        """Scrape a single source with retry logic."""
        return scraper.scrape(hours=hours)

    def _step_enrich(self, run_id: str) -> Dict[str, Any]:
        """Step 2: Enrich scraped items that lack full content."""
        logger.info("[2/5] Enriching content...")
        self.repo.update_pipeline_run(run_id, current_step=STEP_ENRICH)

        items = self.repo.get_scraped_content_without_enrichment()
        enriched = 0
        failed = 0

        for item in items:
            scraper = self.registry.get(item.source_type)
            if not scraper:
                continue
            try:
                scraped_item = ScrapedItem(
                    source_id=item.source_id,
                    source_type=item.source_type,
                    title=item.title,
                    url=item.url,
                    description=item.description or "",
                    published_at=item.published_at,
                )
                enriched_item = scraper.enrich(scraped_item)
                if enriched_item.content:
                    self.repo.update_scraped_content(item.id, enriched_item.content)
                    enriched += 1
            except Exception as e:
                logger.warning(f"Failed to enrich {item.id}: {e}")
                failed += 1

        self.repo.update_pipeline_run(run_id, articles_enriched=enriched)
        logger.info(f"  Enriched: {enriched}, Failed: {failed}")

        return {"status": "success", "enriched": enriched, "failed": failed}

    def _step_digest(self, run_id: str) -> Dict[str, Any]:
        """Step 3: Generate AI digests for unprocessed articles."""
        logger.info("[3/5] Generating AI digests...")
        self.repo.update_pipeline_run(run_id, current_step=STEP_DIGEST)

        agent = DigestAgent()
        articles = self.repo.get_articles_without_digest()
        total = len(articles)
        processed = 0
        failed = 0

        for idx, article in enumerate(articles, 1):
            title_short = article["title"][:50] + "..." if len(article["title"]) > 50 else article["title"]
            logger.info(f"  [{idx}/{total}] {article['type']}: {title_short}")

            try:
                digest = agent.generate_digest(
                    title=article["title"],
                    content=article["content"],
                    article_type=article["type"],
                )
                if digest:
                    self.repo.create_digest(
                        article_type=article["type"],
                        article_id=article["id"],
                        url=article["url"],
                        title=digest.title,
                        summary=digest.summary,
                        published_at=article.get("published_at"),
                    )
                    processed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"  ✗ Error: {e}")
                failed += 1

        self.repo.update_pipeline_run(run_id, digests_created=processed)
        logger.info(f"  Digests: {processed} created, {failed} failed out of {total}")

        return {"status": "success", "total": total, "processed": processed, "failed": failed}

    def _step_curate(self, run_id: str, hours: int) -> Dict[str, Any]:
        """Step 4: Rank digests by user relevance."""
        logger.info("[4/5] Curating and ranking digests...")
        self.repo.update_pipeline_run(run_id, current_step=STEP_CURATE)

        curator = CuratorAgent(USER_PROFILE)
        digests = self.repo.get_recent_digests(hours=hours)

        if not digests:
            logger.warning("  No digests to curate")
            return {"status": "success", "total": 0, "ranked": 0}

        ranked = curator.rank_digests(digests)

        # Store ranking results
        for article in ranked:
            self.repo.update_digest_ranking(
                article.digest_id, article.relevance_score, article.rank
            )

        logger.info(f"  Ranked {len(ranked)} articles")
        return {"status": "success", "total": len(digests), "ranked": len(ranked)}

    def _step_deliver(self, run_id: str, hours: int, top_n: int) -> Dict[str, Any]:
        """Step 5: Compose and send email newsletter."""
        logger.info("[5/5] Composing and sending email...")
        self.repo.update_pipeline_run(run_id, current_step=STEP_DELIVER)

        curator = CuratorAgent(USER_PROFILE)
        email_agent = EmailAgent(USER_PROFILE)
        digests = self.repo.get_recent_digests(hours=hours)

        if not digests:
            logger.warning("  No digests available for email")
            self.repo.update_pipeline_run(run_id, email_sent="false")
            return {"status": "skipped", "reason": "no digests"}

        ranked = curator.rank_digests(digests)
        if not ranked:
            self.repo.update_pipeline_run(run_id, email_sent="false")
            return {"status": "failed", "reason": "ranking failed"}

        article_details = [
            RankedArticleDetail(
                digest_id=a.digest_id, rank=a.rank,
                relevance_score=a.relevance_score, reasoning=a.reasoning,
                title=next((d["title"] for d in digests if d["id"] == a.digest_id), ""),
                summary=next((d["summary"] for d in digests if d["id"] == a.digest_id), ""),
                url=next((d["url"] for d in digests if d["id"] == a.digest_id), ""),
                article_type=next((d["article_type"] for d in digests if d["id"] == a.digest_id), ""),
            )
            for a in ranked
        ]

        email_digest = email_agent.create_email_digest_response(
            ranked_articles=article_details,
            total_ranked=len(ranked),
            limit=top_n,
        )

        markdown_content = email_digest.to_markdown()
        html_content = digest_to_html(email_digest)
        subject = f"AI News Digest — {datetime.now(timezone.utc).strftime('%B %d, %Y')}"

        send_email(subject=subject, body_text=markdown_content, body_html=html_content)

        self.repo.update_pipeline_run(run_id, email_sent="true")
        logger.info(f"  ✓ Email sent: {subject}")

        return {"status": "success", "articles_count": len(email_digest.articles)}
