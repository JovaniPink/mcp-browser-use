# -*- coding: utf-8 -*-

"""Backwards-compatible browser wrapper built on top of BrowserSession.

This module previously provided a rich Playwright-based implementation. The
latest versions of ``browser-use`` have consolidated this behavior inside the
``BrowserSession`` class. To keep imports working for downstream users we map
the legacy ``BrowserConfig`` style into the new ``BrowserSession`` constructor.
"""

from __future__ import annotations

from typing import Any, Dict

from browser_use import BrowserSession


def _config_to_kwargs(config: Any | None) -> Dict[str, Any]:
    """Translate legacy ``BrowserConfig`` objects into BrowserSession kwargs."""

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


class CustomBrowser(BrowserSession):
    """Thin wrapper around :class:`browser_use.BrowserSession` for compatibility."""

    def __init__(self, config: Any | None = None, **kwargs: Any) -> None:
        session_kwargs = {k: v for k, v in _config_to_kwargs(config).items() if v is not None}
        session_kwargs.update({k: v for k, v in kwargs.items() if v is not None})
        super().__init__(**session_kwargs)
