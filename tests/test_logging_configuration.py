"""Smoke tests around module imports and logging configuration."""

import importlib
import logging
import sys

import pytest


@pytest.mark.parametrize(
    "module_name",
    (
        "mcp_browser_use.browser.browser_manager",
        "mcp_browser_use.client",
        "mcp_browser_use.server",
        "mcp_browser_use.utils.llm",
    ),
)
def test_module_import_does_not_call_basic_config(module_name, monkeypatch):
    importlib.import_module(module_name)
    sys.modules.pop(module_name, None)
    calls = []
    monkeypatch.setattr(logging, "basicConfig", lambda *args, **kwargs: calls.append(1))

    importlib.import_module(module_name)

    assert calls == []
