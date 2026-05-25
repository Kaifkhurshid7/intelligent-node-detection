"""
Structured logging configuration.

Provides a consistent logging interface across the application
with appropriate formatting for development and production.
"""

import logging
import sys

from app.core.config import LOG_LEVEL, DEBUG


def setup_logging() -> logging.Logger:
    """
    Configure and return the application logger.

    Uses a simple format for development (DEBUG=true) and a more
    structured format for production environments.
    """
    logger = logging.getLogger("node_detection")
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    # Avoid duplicate handlers on reload
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    logger.addHandler(handler)
    return logger


logger = setup_logging()
