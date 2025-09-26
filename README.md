# MCP Browser Use Server

[![smithery badge](https://smithery.ai/badge/@JovaniPink/mcp-browser-use)](https://smithery.ai/server/@JovaniPink/mcp-browser-use)

> Model Context Protocol (MCP) server that wires [browser-use](https://github.com/browser-use/browser-use) into Claude Desktop and other MCP compatible clients.

<a href="https://glama.ai/mcp/servers/tjea5rgnbv"><img width="380" height="200" src="https://glama.ai/mcp/servers/tjea5rgnbv/badge" alt="Browser Use Server MCP server" /></a>

## Overview

This repository provides a production-ready wrapper around the `browser-use` automation engine. It exposes a single MCP tool (`run_browser_agent`) that orchestrates a browser session, executes the `browser-use` agent, and returns the final result back to the client. The refactored layout focuses on keeping configuration in one place, improving testability, and keeping `browser-use` upgrades isolated from MCP specific code.

### Key Capabilities

- **Automated browsing** – Navigate, interact with forms, control tabs, capture screenshots, and read page content through natural-language instructions executed by `browser-use`.
- **Agent lifecycle management** – `CustomAgent` wraps `browser-use`'s base agent to add history export, richer prompts, and consistent error handling across runs.
- **Centralised browser configuration** – `create_browser_session` translates environment variables into a ready-to-use `BrowserSession`, enabling persistent profiles, proxies, and custom Chromium flags without touching the agent logic.
- **FastMCP integration** – `server.py` registers the MCP tool, normalises configuration, and ensures the browser session is always cleaned up.
- **Client helpers** – `client.py` includes async helpers for tests or other Python processes that wish to exercise the MCP server in-process.

### Project Structure

```
.
├── documentation/
│   ├── CONFIGURATION.md      # Detailed configuration reference
│   └── SECURITY.md           # Security considerations for running the server
├── sample.env.env            # Example environment variables for local development
├── src/mcp_browser_use/
│   ├── agent/                # Custom agent, prompts, message history, and views
│   ├── browser/              # Browser session factory and persistence helpers
│   ├── controller/           # Custom controller extensions for clipboard actions
│   ├── utils/                # LLM factory, agent state helpers, encoding utilities
│   ├── client.py             # Async helper for connecting to the FastMCP app
│   └── server.py             # FastMCP app and the `run_browser_agent` tool
└── tests/                    # Unit tests covering server helpers and agent features
```

## Getting Started

### Requirements

- Python 3.11+
- Google Chrome or Chromium (for local automation)
- [`uv`](https://github.com/astral-sh/uv) for dependency management (recommended)
- Optional: Claude Desktop or another MCP-compatible client for integration testing

### Installation

```bash
git clone https://github.com/JovaniPink/mcp-browser-use.git
cd mcp-browser-use
uv sync
```

Copy `sample.env.env` to `.env` (or export the variables in another way) and update the values for the providers you plan to use.

### Launching the server

```bash
uv run mcp-browser-use
```

The command invokes the console script defined in `pyproject.toml`, starts the FastMCP application, and registers the `run_browser_agent` tool.

#### Using with Claude Desktop

Once the server is running you can register it inside Claude Desktop, for example:

```json
"mcpServers": {
  "mcp_server_browser_use": {
    "command": "uvx",
    "args": ["mcp-server-browser-use"],
    "env": {
      "MCP_MODEL_PROVIDER": "anthropic",
      "MCP_MODEL_NAME": "claude-3-5-sonnet-20241022"
    }
  }
}
```

### Debugging

For interactive debugging, use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/project run mcp-browser-use
```

The inspector prints a URL that can be opened in the browser to watch tool calls and responses in real time.

## Configuration

A full list of environment variables and their defaults is available in [documentation/CONFIGURATION.md](documentation/CONFIGURATION.md). Highlights include:

- `MCP_MODEL_PROVIDER`, `MCP_MODEL_NAME`, `MCP_TEMPERATURE`, `MCP_MAX_STEPS`, `MCP_MAX_ACTIONS_PER_STEP`, and `MCP_USE_VISION` control the LLM and agent run.
- Provider-specific API keys and endpoints (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `GOOGLE_API_KEY`, `AZURE_OPENAI_API_KEY`, etc.).
- Browser runtime flags (`BROWSER_USE_HEADLESS`, `BROWSER_USE_EXTRA_CHROMIUM_ARGS`, `CHROME_PERSISTENT_SESSION`, `BROWSER_USE_PROXY_URL`, ...).

Use `.env` + [`python-dotenv`](https://pypi.org/project/python-dotenv/) or your preferred secrets manager to keep credentials out of source control.

## Running Tests

```bash
uv run pytest
```

The tests cover the custom agent behaviour, browser session factory, and other utility helpers.

## Security

Controlling a full browser instance remotely can grant broad access to the host machine. Review [documentation/SECURITY.md](documentation/SECURITY.md) before exposing the server to untrusted environments.

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Open a pull request

Bug reports and feature suggestions are welcome—please include logs and reproduction steps when applicable.
