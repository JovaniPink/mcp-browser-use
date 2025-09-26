# -*- coding: utf-8 -*-
"""Utility helpers for configuring and creating :class:`BrowserSession` instances.

This module consolidates the thin wrappers that previously lived in
``custom_browser.py``, ``custom_context.py``, and ``config.py``.  The new structure
centralises environment parsing so ``server.py`` can simply request a configured
browser session without re-implementing the translation from environment
variables to ``BrowserSession`` keyword arguments.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from browser_use import BrowserSession
from browser_use.browser.profile import ProxySettings

logger = logging.getLogger(__name__)

_BOOL_TRUE = {"1", "true", "yes", "on"}


@dataclass(slots=True)
class BrowserPersistenceConfig:
    """Configuration for browser persistence and remote debugging settings."""

    persistent_session: bool = False
    user_data_dir: Optional[str] = None
    debugging_port: Optional[int] = None
    debugging_host: Optional[str] = None

    @classmethod
    def from_env(cls) -> "BrowserPersistenceConfig":
        persistent_session = os.getenv("CHROME_PERSISTENT_SESSION", "").lower() in _BOOL_TRUE
        user_data_dir = os.getenv("CHROME_USER_DATA") or None

        debugging_port: Optional[int]
        port_value = os.getenv("CHROME_DEBUGGING_PORT")
        if port_value:
            try:
                debugging_port = int(port_value)
            except ValueError:
                logger.warning(
                    "Invalid CHROME_DEBUGGING_PORT=%r, ignoring debug port setting.",
                    port_value,
                )
                debugging_port = None
        else:
            debugging_port = None

        debugging_host = os.getenv("CHROME_DEBUGGING_HOST") or None

        return cls(
            persistent_session=persistent_session,
            user_data_dir=user_data_dir,
            debugging_port=debugging_port,
            debugging_host=debugging_host,
        )


@dataclass(slots=True)
class BrowserEnvironmentConfig:
    """All runtime settings required for instantiating ``BrowserSession``."""

    headless: bool = False
    disable_security: bool = False
    executable_path: Optional[str] = None
    args: Optional[list[str]] = None
    allowed_domains: Optional[list[str]] = None
    proxy: Optional[ProxySettings] = None
    cdp_url: Optional[str] = None
    user_data_dir: Optional[str] = None

    def to_kwargs(self) -> Dict[str, Any]:
        """Convert to keyword arguments understood by :class:`BrowserSession`."""

        kwargs: Dict[str, Any] = {
            "headless": self.headless,
            "disable_security": self.disable_security,
            "executable_path": self.executable_path,
            "args": self.args,
            "allowed_domains": self.allowed_domains,
            "proxy": self.proxy,
            "cdp_url": self.cdp_url,
            "user_data_dir": self.user_data_dir,
        }
        # Remove ``None`` values so BrowserSession can rely on its defaults.
        return {key: value for key, value in kwargs.items() if value is not None}

    @classmethod
    def from_env(cls) -> "BrowserEnvironmentConfig":
        persistence = BrowserPersistenceConfig.from_env()

        headless = os.getenv("BROWSER_USE_HEADLESS", "false").lower() in _BOOL_TRUE
        disable_security = os.getenv("BROWSER_USE_DISABLE_SECURITY", "false").lower() in _BOOL_TRUE
        executable_path = os.getenv("CHROME_PATH") or None

        extra_args_env = os.getenv("BROWSER_USE_EXTRA_CHROMIUM_ARGS")
        args = None
        if extra_args_env:
            args = [arg.strip() for arg in extra_args_env.split(",") if arg.strip()]

        allowed_domains_env = os.getenv("BROWSER_USE_ALLOWED_DOMAINS")
        allowed_domains = None
        if allowed_domains_env:
            allowed_domains = [
                domain.strip()
                for domain in allowed_domains_env.split(",")
                if domain.strip()
            ]

        proxy_url = os.getenv("BROWSER_USE_PROXY_URL")
        proxy: Optional[ProxySettings] = None
        if proxy_url:
            proxy = ProxySettings(
                server=proxy_url,
                bypass=os.getenv("BROWSER_USE_NO_PROXY"),
                username=os.getenv("BROWSER_USE_PROXY_USERNAME"),
                password=os.getenv("BROWSER_USE_PROXY_PASSWORD"),
            )

        cdp_url = os.getenv("BROWSER_USE_CDP_URL") or None

        user_data_dir = None
        if persistence.persistent_session:
            if persistence.user_data_dir:
                user_data_dir = persistence.user_data_dir
            else:
                logger.warning(
                    "CHROME_PERSISTENT_SESSION requested but CHROME_USER_DATA was not provided."
                )

        return cls(
            headless=headless,
            disable_security=disable_security,
            executable_path=executable_path,
            args=args,
            allowed_domains=allowed_domains,
            proxy=proxy,
            cdp_url=cdp_url,
            user_data_dir=user_data_dir,
        )


def create_browser_session(overrides: Optional[Dict[str, Any]] = None) -> BrowserSession:
    """Instantiate a :class:`BrowserSession` using environment defaults.

    ``overrides`` can be supplied to fine-tune the resulting session.  Any keys
    set to ``None`` are ignored so callers can override only a subset of values.
    """

    config = BrowserEnvironmentConfig.from_env()
    kwargs = config.to_kwargs()

    if overrides:
        for key, value in overrides.items():
            if value is not None:
                kwargs[key] = value
            elif key in kwargs:
                # Explicit ``None`` removes the override letting BrowserSession
                # fall back to its internal default.
                kwargs.pop(key)

    logger.debug("Creating BrowserSession with kwargs: %s", {k: v for k, v in kwargs.items() if k != "proxy"})
    return BrowserSession(**kwargs)
