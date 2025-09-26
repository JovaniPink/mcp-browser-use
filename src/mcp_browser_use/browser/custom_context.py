# -*- coding: utf-8 -*-

"""Compatibility shim providing a context-like wrapper around ``Browser`` pages."""

from __future__ import annotations

from typing import Any, Dict

from .custom_browser import CustomBrowser


def _config_to_kwargs(config: Any | None) -> Dict[str, Any]:
    if config is None:
        return {}

    return {
        key: getattr(config, key)
        for key in ("trace_path", "save_recording_path", "no_viewport")
        if hasattr(config, key) and getattr(config, key) is not None
    }


class CustomBrowserContext:
    """Placeholder context that proxies to ``Browser`` pages."""

    def __init__(self, browser: CustomBrowser, config: Any | None = None) -> None:
        self._browser = browser
        self._config = _config_to_kwargs(config)
        self._page: Any | None = None

    async def ensure_page(self) -> Any:
        if self._page is None:
            self._page = await self._browser.new_page(**self._config)
        return self._page

    async def close(self) -> None:
        if self._page and hasattr(self._page, "close"):
            await self._page.close()
        self._page = None

    def __getattr__(self, name: str) -> Any:
        page = self._page
        if page is None:
            raise AttributeError(name)
        return getattr(page, name)
