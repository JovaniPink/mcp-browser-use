"""Tests for browser manager environment configuration helpers."""

from __future__ import annotations

import importlib
import logging

import pytest
from browser_use.browser.profile import BrowserProfile

browser_manager = importlib.import_module("mcp_browser_use.browser.browser_manager")


@pytest.fixture(autouse=True)
def clear_browser_env(monkeypatch):
    """Ensure browser-related environment variables do not leak between tests."""

    for key in (
        "BROWSER_USE_CDP_URL",
        "CHROME_DEBUGGING_HOST",
        "CHROME_DEBUGGING_PORT",
        "BROWSER_USE_ALLOWED_DOMAINS",
        "BROWSER_USE_EXTRA_CHROMIUM_ARGS",
        "CHROME_PATH",
        "CHROME_PERSISTENT_SESSION",
        "CHROME_USER_DATA",
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

    session = browser_manager.create_browser_session()

    assert session.cdp_url == "http://localhost:9000"


def test_create_browser_session_redacts_cdp_url_from_debug_log(monkeypatch, caplog):
    """Credential-bearing CDP URLs are passed through but never logged."""

    cdp_url = "wss://user:secret@browser.example/devtools?token=sensitive"
    monkeypatch.setenv("BROWSER_USE_CDP_URL", cdp_url)

    with caplog.at_level(logging.DEBUG, logger=browser_manager.__name__):
        session = browser_manager.create_browser_session()

    assert session.cdp_url == cdp_url
    assert "secret" not in caplog.text
    assert "sensitive" not in caplog.text
    assert "'cdp_url': '<redacted>'" in caplog.text


def test_local_allowlist_starts_blank_without_mutating_user_args(monkeypatch):
    monkeypatch.setenv("BROWSER_USE_ALLOWED_DOMAINS", "example.com")
    caller_args = ["--disable-notifications"]

    session = browser_manager.create_browser_session({"args": caller_args})

    assert session.is_local
    assert session.browser_profile.allowed_domains == ["example.com"]
    assert session.browser_profile.args == [
        "--disable-notifications",
        "--no-startup-window",
    ]
    assert caller_args == ["--disable-notifications"]


def test_allowlist_preserves_environment_launch_args(monkeypatch):
    monkeypatch.setenv("BROWSER_USE_ALLOWED_DOMAINS", "example.com")
    monkeypatch.setenv(
        "BROWSER_USE_EXTRA_CHROMIUM_ARGS", "--disable-notifications,--lang=en-US"
    )

    session = browser_manager.create_browser_session()

    assert session.browser_profile.args == [
        "--disable-notifications",
        "--lang=en-US",
        "--no-startup-window",
    ]


@pytest.mark.parametrize("flag", ["--no-startup-window", "--no-startup-window=true"])
def test_existing_startup_flag_is_preserved_once(flag):
    caller_args = ["--disable-notifications", flag]

    session = browser_manager.create_browser_session(
        {"allowed_domains": ["example.com"], "args": caller_args}
    )

    assert session.browser_profile.args == caller_args
    assert caller_args == ["--disable-notifications", flag]


@pytest.mark.parametrize(
    "mode",
    [
        {"allowed_domains": []},
        {"cdp_url": "http://127.0.0.1:9222", "is_local": True},
        {"use_cloud": True},
        {"cloud_browser": True},
        {"cloud_browser_params": {}},
        {"cloud_timeout": 30},
        {"profile_id": "00000000-0000-0000-0000-000000000001"},
    ],
    ids=[
        "unrestricted",
        "attached-local-cdp",
        "cloud",
        "cloud-alias",
        "cloud-params",
        "cloud-timeout",
        "cloud-profile",
    ],
)
def test_factory_does_not_change_remote_cloud_or_unrestricted_args(mode):
    caller_args = ["--disable-notifications"]

    session = browser_manager.create_browser_session(
        {"allowed_domains": ["example.com"], "args": caller_args, **mode}
    )

    assert session.browser_profile.args == caller_args
    assert caller_args == ["--disable-notifications"]
    if "cdp_url" in mode:
        assert session.cdp_url == mode["cdp_url"]


def test_local_supplied_profile_is_copied_before_args_adaptation():
    caller_args = ["--disable-notifications"]
    profile = BrowserProfile(allowed_domains=["example.com"], args=caller_args)

    session = browser_manager.create_browser_session({"browser_profile": profile})

    assert session.browser_profile is not profile
    assert session.browser_profile.args == [*caller_args, "--no-startup-window"]
    assert profile.args == caller_args == ["--disable-notifications"]


def test_allowlisted_local_launch_preserves_persistent_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("BROWSER_USE_ALLOWED_DOMAINS", "example.com")
    monkeypatch.setenv("CHROME_PERSISTENT_SESSION", "true")
    monkeypatch.setenv("CHROME_USER_DATA", str(tmp_path))

    session = browser_manager.create_browser_session()

    assert session.is_local
    assert session.browser_profile.user_data_dir == tmp_path
    assert "--no-startup-window" in session.browser_profile.args


@pytest.mark.parametrize(
    "mode", [{"cdp_url": "http://127.0.0.1:9222"}, {"use_cloud": True}]
)
def test_remote_supplied_profile_preserves_args(mode):
    caller_args = ["--disable-notifications"]
    profile = BrowserProfile(allowed_domains=["example.com"], args=caller_args, **mode)

    session = browser_manager.create_browser_session({"browser_profile": profile})

    assert session.browser_profile.args == profile.args == caller_args
    if "cdp_url" in mode:
        assert session.cdp_url == mode["cdp_url"]
