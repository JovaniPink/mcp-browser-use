"""Public package surface for the MCP browser-use server."""

from __future__ import annotations

import os
from importlib import import_module

# Prevent browser-use from installing its own handlers in an MCP stdio process.
os.environ.setdefault("BROWSER_USE_SETUP_LOGGING", "false")

__all__ = [
    "AgentNotRegisteredError",
    "app",
    "create_client_session",
    "launch_mcp_browser_use_server",
]


def __getattr__(name: str):
    if name in {"AgentNotRegisteredError", "create_client_session"}:
        return getattr(import_module("mcp_browser_use.client"), name)
    if name in {"app", "launch_mcp_browser_use_server"}:
        return getattr(import_module("mcp_browser_use.server"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
