# app/core/logging.py
"""
Structured Logging Setup

Every log line automatically includes:
- timestamp (ISO format)
- log level
- filename and line number (in development)

In development: colored, human-readable output
In production: JSON format for log aggregation (CloudWatch, Loki, etc.)
"""
import logging

import structlog

from app.core.settings import get_settings


def setup_logging() -> None:
    """
    Configure structured logging for the entire application.

    Call this once at application startup.
    After this, any code can do:
        logger = structlog.get_logger()
        logger.info("Something happened", key="value")
    And it will automatically include request_id, correlation_id, timestamp.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.environment.upper(), logging.INFO)

    # Configure Python's standard logging
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        force=True,
    )

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Choose renderer based on environment
    if settings.environment.lower() == "development":
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    # Build the processor chain
    # Each processor transforms the log event dict before rendering
    processors = [
        # Add log level name
        structlog.stdlib.add_log_level,
        # Add ISO timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Handle exceptions nicely
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        # Final rendering
        renderer,
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
