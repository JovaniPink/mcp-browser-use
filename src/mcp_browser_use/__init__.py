# -*- coding: utf-8 -*-

"""MCP server for browser-use."""

from mcp_browser_use.mcp_browser_use import (  # noqa: F401
    AgentNotRegisteredError,
    create_client_session,
)
from mcp_browser_use.server import app, main

__all__ = ["app", "main", "create_client_session", "AgentNotRegisteredError"]
