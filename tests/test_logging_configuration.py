"""Smoke tests around module imports and logging configuration."""

from __future__ import annotations

import importlib
import logging
import sys
from typing import Iterable

import pytest


MODULES_TO_TEST: Iterable[str] = (
    "mcp_browser_use.controller.custom_controller",
    "mcp_browser_use.utils.utils",
    "mcp_browser_use.agent.custom_agent",
    "mcp_browser_use.agent.custom_massage_manager",
)


@pytest.mark.parametrize("module_name", MODULES_TO_TEST)
def test_module_import_does_not_call_basic_config(module_name: str, monkeypatch) -> None:
    """Ensure importing project modules does not invoke ``logging.basicConfig``."""

    # Import once so that shared third-party dependencies are cached.
    importlib.import_module(module_name)
    sys.modules.pop(module_name, None)

    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def record_basic_config(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))

    monkeypatch.setattr(logging, "basicConfig", record_basic_config)

    importlib.import_module(module_name)

    assert calls == [], f"Module {module_name} should not call logging.basicConfig during import"
