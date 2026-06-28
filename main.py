"""
AI Newsletter Agent — Entry Point

Runs the full AI newsletter pipeline:
1. Scrape content from all registered sources
2. Enrich content (transcripts, markdown)
3. Generate AI digests
4. Curate and rank by user relevance
5. Compose and deliver email newsletter

Usage:
    # Default: last 24 hours, top 10 articles
    uv run python main.py

    # Custom: last 48 hours, top 5 articles
    uv run python main.py 48 5

    # Scrape and digest only (no email)
    uv run python main.py --no-email
"""

import sys

from dotenv import load_dotenv

load_dotenv()

from app.logging_config import setup_logging
from app.pipeline.orchestrator import PipelineOrchestrator


def main(hours: int = 24, top_n: int = 10, send_email: bool = True) -> dict:
    """Run the full AI newsletter pipeline."""
    setup_logging(level="INFO")

    orchestrator = PipelineOrchestrator()
    return orchestrator.run(hours=hours, top_n=top_n, send_email_flag=send_email)


if __name__ == "__main__":
    hours = 24
    top_n = 10
    send_email = True

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    if len(args) > 0:
        hours = int(args[0])
    if len(args) > 1:
        top_n = int(args[1])
    if "--no-email" in flags:
        send_email = False

    result = main(hours=hours, top_n=top_n, send_email=send_email)
    exit(0 if result.get("status") == "success" else 1)
