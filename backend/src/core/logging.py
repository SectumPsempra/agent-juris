"""Structured logging configuration using structlog.

Call ``configure_logging()`` once at application startup before any log
statements are emitted.  Afterwards, obtain a logger anywhere with::

    from src.core.logging import get_logger
    logger = get_logger(__name__)
"""

import logging
import sys

import structlog

from src.core.config import settings

_SHARED_PROCESSORS: list = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
]


def configure_logging() -> None:
    """Wire structlog and stdlib logging together.

    In production the output is newline-delimited JSON suitable for ingestion
    by any log aggregator.  In other environments the human-readable console
    renderer is used instead.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    if settings.app_env == "production":
        final_processors: list = _SHARED_PROCESSORS + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        final_processors = _SHARED_PROCESSORS + [
            structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ]

    structlog.configure(
        processors=final_processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Redirect stdlib loggers (uvicorn, sqlalchemy, etc.) through structlog.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def get_logger(name: str = "") -> structlog.BoundLogger:
    """Return a bound structlog logger.

    Pass ``name`` (typically ``__name__``) to identify the originating module
    in log output.
    """
    return structlog.get_logger(name)
