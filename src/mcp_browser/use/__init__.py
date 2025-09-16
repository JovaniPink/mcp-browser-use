"""Backwards compatible accessors for the ``mcp_browser.use`` namespace."""

from __future__ import annotations

from .mcp_browser_use import AgentNotRegisteredError, create_client_session

__all__ = ["AgentNotRegisteredError", "create_client_session"]
