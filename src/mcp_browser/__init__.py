"""Compatibility namespace for the historic ``mcp_browser.use`` package."""

from __future__ import annotations

from mcp_browser_use import (
    AgentNotRegisteredError,
    app,
    create_client_session,
    main,
)

__all__ = ["AgentNotRegisteredError", "app", "create_client_session", "main"]
