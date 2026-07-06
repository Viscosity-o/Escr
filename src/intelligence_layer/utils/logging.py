"""
utils/logging.py
================
Centralized logging configuration for the module.

Provides a factory function that returns a consistently configured logger,
ensuring all components log in the same structured format.
"""
import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger configured with a consistent format.

    Usage:
        from intelligence_layer.utils.logging import get_logger
        logger = get_logger(__name__)

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
