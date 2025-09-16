"""Compatibility shim forwarding to :mod:`mcp_browser_use`."""

from __future__ import annotations

from mcp_browser_use.mcp_browser_use import (  # noqa: F401
    AgentNotRegisteredError,
    create_client_session,
)

__all__ = ["AgentNotRegisteredError", "create_client_session"]
