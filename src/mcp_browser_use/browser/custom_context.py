# -*- coding: utf-8 -*-

"""Lightweight compatibility layer for legacy BrowserContext imports."""

from __future__ import annotations

from typing import Any

from browser_use import BrowserSession


class CustomBrowserContext:
    """Placeholder context that proxies to :class:`BrowserSession` methods."""

    def __init__(self, browser: BrowserSession, config: Any | None = None) -> None:
        self.browser = browser
        self.config = config

    async def close(self) -> None:  # pragma: no cover - compatibility shim
        """Compatibility shim: closing a context is a no-op with BrowserSession."""
        return None
