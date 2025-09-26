"""Centralised logging configuration utilities for the MCP browser agent."""

from __future__ import annotations

import logging
import os
from typing import Optional


_DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def _resolve_level(level_name: Optional[str]) -> int:
    """Translate a string level name into a numeric logging level."""

    if not level_name:
        return logging.INFO

    if level_name.isdigit():
        return int(level_name)

    resolved = logging.getLevelName(level_name.upper())
    if isinstance(resolved, int):
        return resolved
    return logging.INFO


def configure_logging() -> None:
    """Configure the root logger once for the application."""

    level = _resolve_level(os.getenv("LOG_LEVEL"))

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=level, format=_DEFAULT_FORMAT)
    else:
        root_logger.setLevel(level)
