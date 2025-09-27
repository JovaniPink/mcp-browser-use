"""Tests for browser manager environment configuration helpers."""

from __future__ import annotations

import importlib

import pytest


browser_manager = importlib.import_module(
    "mcp_browser_use.browser.browser_manager"
)


@pytest.fixture(autouse=True)
def clear_browser_env(monkeypatch):
    """Ensure browser-related environment variables do not leak between tests."""

    for key in (
        "BROWSER_USE_CDP_URL",
        "CHROME_DEBUGGING_HOST",
        "CHROME_DEBUGGING_PORT",
    ):
        monkeypatch.delenv(key, raising=False)


def test_from_env_derives_cdp_url_from_debugging(monkeypatch):
    """When only debugging env vars are set, derive a CDP URL automatically."""

    monkeypatch.setenv("CHROME_DEBUGGING_HOST", "debug.example")
    monkeypatch.setenv("CHROME_DEBUGGING_PORT", "1337")

    config = browser_manager.BrowserEnvironmentConfig.from_env()

    assert config.cdp_url == "http://debug.example:1337"


def test_create_browser_session_preserves_computed_cdp_url(monkeypatch):
    """Computed CDP URL is passed to BrowserSession when overrides omit it."""

    monkeypatch.setenv("CHROME_DEBUGGING_HOST", "localhost")
    monkeypatch.setenv("CHROME_DEBUGGING_PORT", "9000")

    captured_kwargs: dict[str, object] = {}

    class DummyBrowserSession:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    monkeypatch.setattr(browser_manager, "BrowserSession", DummyBrowserSession)

    session = browser_manager.create_browser_session()

    assert isinstance(session, DummyBrowserSession)
    assert captured_kwargs["cdp_url"] == "http://localhost:9000"
