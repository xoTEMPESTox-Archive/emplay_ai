"""Structured logging configuration for RFP Intelligence Platform."""

import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a standard structured logger instance.

    Args:
        name: Name of the logger, typically __name__.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name or "rfp_intelligence")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
