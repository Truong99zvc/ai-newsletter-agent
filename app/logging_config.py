"""
Centralized logging configuration for the AI Newsletter Agent.

Provides consistent, structured logging across all modules with:
- JSON-compatible structured format for production
- Human-readable format for development
- Configurable log levels per module
"""

import logging
import sys
from typing import Optional


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO", module_levels: Optional[dict] = None) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Root log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        module_levels: Optional per-module log level overrides
            e.g., {"app.scrapers": "DEBUG", "sqlalchemy.engine": "WARNING"}
    """
    root_logger = logging.getLogger()

    # Prevent duplicate handlers on re-initialization
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT))

    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    for noisy_logger in [
        "httpx",
        "httpcore",
        "openai",
        "urllib3",
        "feedparser",
        "sqlalchemy.engine",
    ]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    # Apply per-module overrides
    if module_levels:
        for module, mod_level in module_levels.items():
            logging.getLogger(module).setLevel(
                getattr(logging, mod_level.upper(), logging.INFO)
            )


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger for a module.

    Usage:
        from app.logging_config import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)
