# -*- coding: utf-8 -*-

"""Backwards-compatible browser wrapper built on top of the modern Browser API.

This module previously provided a Playwright-based implementation that relied on
``BrowserConfig`` objects. Since ``browser-use`` 0.7 the public API exposes a
``Browser`` class directly, so we translate any legacy configuration into the
new keyword arguments and provide a few helper aliases (``close`` and
``new_context``) for code that still expects the older surface.
"""

from __future__ import annotations

from typing import Any, Dict

from browser_use import Browser


def _config_to_kwargs(config: Any | None) -> Dict[str, Any]:
    """Translate legacy ``BrowserConfig`` objects into ``Browser`` kwargs."""

    if config is None:
        return {}

    return {
        "headless": getattr(config, "headless", None),
        "disable_security": getattr(config, "disable_security", None),
        "executable_path": getattr(config, "chrome_instance_path", None),
        "args": getattr(config, "extra_chromium_args", None),
        "cdp_url": getattr(config, "wss_url", None),
        "proxy": getattr(config, "proxy", None),
        "allowed_domains": getattr(config, "allowed_domains", None),
    }


class CustomBrowser(Browser):
    """Thin wrapper around :class:`browser_use.Browser` for compatibility."""

    def __init__(self, config: Any | None = None, **kwargs: Any) -> None:
        normalized_kwargs = {k: v for k, v in _config_to_kwargs(config).items() if v is not None}
        normalized_kwargs.update({k: v for k, v in kwargs.items() if v is not None})
        super().__init__(**normalized_kwargs)

    async def close(self) -> None:
        """Alias for :meth:`Browser.stop` kept for backwards compatibility."""

        await self.stop()

    async def new_context(self, *args: Any, **kwargs: Any) -> Any:
        """Alias for :meth:`Browser.new_page` for backwards compatibility."""

        return await super().new_page(*args, **kwargs)
