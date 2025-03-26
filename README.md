# MCP server w/ Browser Use

[![smithery badge](https://smithery.ai/badge/@JovaniPink/mcp-browser-use)](https://smithery.ai/server/@JovaniPink/mcp-browser-use)

> MCP server for [browser-use](https://github.com/browser-use/browser-use).

<a href="https://glama.ai/mcp/servers/tjea5rgnbv"><img width="380" height="200" src="https://glama.ai/mcp/servers/tjea5rgnbv/badge" alt="Browser Use Server MCP server" /></a>

## Overview

This repository contains the server for the [browser-use](https://github.com/browser-use/browser-use) library, which provides a powerful browser automation system that enables AI agents to interact with web browsers through natural language. The server is built on Anthropic's [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) and provides a seamless integration with the [browser-use](https://github.com/browser-use/browser-use) library.

## Features

1. **Browser Control**

- Automated browser interactions via natural language
- Navigation, form filling, clicking, and scrolling capabilities
- Tab management and screenshot functionality
- Cookie and state management

2. **Agent System**

- Custom agent implementation in custom_agent.py
- Vision-based element detection
- Structured JSON responses for actions
- Message history management and summarization

3. **Configuration**

- Environment-based configuration for API keys and settings
- Chrome browser settings (debugging port, persistence)
- Model provider selection and parameters

## Dependencies

This project relies on the following Python packages:

| Package                                    | Version    | Description                                                                                                                                                                                                   |
| :----------------------------------------- | :--------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Pillow](https://python-pillow.org/)      | >=10.1.0  | Python Imaging Library (PIL) fork that adds image processing capabilities to your Python interpreter.                                                                                                        |
| [browser-use](https://github.com/browser-use/browser-use) | ==0.1.19  | A powerful browser automation system that enables AI agents to interact with web browsers through natural language. The core library that powers this project's browser automation capabilities.      |
| [fastapi](https://fastapi.tiangolo.com/)    | >=0.115.6 | Modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints. Used to create the server that exposes the agent's functionality.                          |
| [fastmcp](https://pypi.org/project/fastmcp/)    | >=0.4.1   | A framework that wraps FastAPI for building MCP (Model Context Protocol) servers.    |
| [instructor](https://github.com/jxnl/instructor)   | >=1.7.2   | Library for structured output prompting and validation with OpenAI models. Enables extracting structured data from model responses.                                                                       |
| [langchain](https://www.langchain.com/)     | >=0.3.14  | Framework for developing applications with large language models (LLMs). Provides tools for chaining together different language model components and interacting with various APIs and data sources.          |
| [langchain-google-genai](https://pypi.org/project/langchain-google-genai/) | >=2.1.1   | LangChain integration for Google GenAI models, enabling the use of Google's generative AI capabilities within the LangChain framework. |
| [langchain-openai](https://api.python.langchain.com/en/latest/langchain_openai.html) | >=0.2.14 | LangChain integrations with OpenAI's models. Enables using OpenAI models (like GPT-4) within the LangChain framework. Used in this project for interacting with OpenAI's language and vision models. |
| [langchain-ollama](https://api.python.langchain.com/en/latest/langchain_ollama/chat_models/ChatOllama.html) | >=0.2.2   | Langchain integration for Ollama, enabling local execution of LLMs. |
| [openai](https://platform.openai.com/docs/api-reference)    | >=1.59.5  | Official Python client library for the OpenAI API. Used to interact directly with OpenAI's models (if needed, in addition to LangChain).                                                                    |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | >=1.0.1   | Reads key-value pairs from a `.env` file and sets them as environment variables. Simplifies local development and configuration management.                                                                 |
| [pydantic](https://docs.pydantic.dev/)       | >=2.10.5  | Data validation and settings management using Python type annotations. Provides runtime enforcement of types and automatic model creation. Essential for defining structured data models in the agent.        |
| [pyperclip](https://pyperclip.readthedocs.io/)   | >=1.9.0   | Cross-platform Python module for copy and paste clipboard functions.                                                                                                                                  |
| [uvicorn](https://www.uvicorn.org/)        | >=0.22.0  | ASGI web server implementation for Python. Used to serve the FastAPI application.                                                                                                                           |

## Components

### Resources

The server implements a browser automation system with:

- Integration with browser-use library for advanced browser control
- Custom browser automation capabilities
- Agent-based interaction system with vision capabilities
- Persistent state management
- Customizable model settings

### Requirements

- Operating Systems (Linux, macOS, Windows; we haven't tested for Docker or Microsoft WSL)
- Python 3.11 or higher
- uv (fast Python package installer)
- Chrome/Chromium browser
- [Claude Desktop](https://claude.ai/download)

### Quick Start

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

#### Installing via Smithery

To install Browser Use for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@JovaniPink/mcp-browser-use):

```bash
npx -y @smithery/cli install @JovaniPink/mcp-browser-use --client claude
```

<details>
  <summary>Development Configuration</summary>

```json
"mcpServers": {
  "mcp_server_browser_use": {
    "command": "uvx",
    "args": [
      "mcp-server-browser-use",
    ],
    "env": {
      "OPENAI_ENDPOINT": "https://api.openai.com/v1",
      "OPENAI_API_KEY": "",
      "ANTHROPIC_API_KEY": "",
      "GOOGLE_API_KEY": "",
      "AZURE_OPENAI_ENDPOINT": "",
      "AZURE_OPENAI_API_KEY": "",
      // "DEEPSEEK_ENDPOINT": "https://api.deepseek.com",
      // "DEEPSEEK_API_KEY": "",
      // Set to false to disable anonymized telemetry
      "ANONYMIZED_TELEMETRY": "false",
      // Chrome settings
      "CHROME_PATH": "",
      "CHROME_USER_DATA": "",
      "CHROME_DEBUGGING_PORT": "9222",
      "CHROME_DEBUGGING_HOST": "localhost",
      // Set to true to keep browser open between AI tasks
      "CHROME_PERSISTENT_SESSION": "false",
      // Model settings
      "MCP_MODEL_PROVIDER": "anthropic",
      "MCP_MODEL_NAME": "claude-3-5-sonnet-20241022",
      "MCP_TEMPERATURE": "0.3",
      "MCP_MAX_STEPS": "30",
      "MCP_USE_VISION": "true",
      "MCP_MAX_ACTIONS_PER_STEP": "5",
      "MCP_TOOL_CALL_IN_CONTENT": "true"
    }
  }
}
```

</details>

### Environment Variables

Key environment variables:

```bash
# API Keys
ANTHROPIC_API_KEY=anthropic_key

# Chrome Configuration
# Optional: Path to Chrome executable
CHROME_PATH=/path/to/chrome
# Optional: Chrome user data directory
CHROME_USER_DATA=/path/to/user/data
# Default: 9222
CHROME_DEBUGGING_PORT=9222
# Default: localhost
CHROME_DEBUGGING_HOST=localhost
# Keep browser open between tasks
CHROME_PERSISTENT_SESSION=false

# Model Settings
# Options: anthropic, openai, azure, deepseek
MCP_MODEL_PROVIDER=anthropic
# Model name
MCP_MODEL_NAME=claude-3-5-sonnet-20241022
MCP_TEMPERATURE=0.3
MCP_MAX_STEPS=30
MCP_USE_VISION=true
MCP_MAX_ACTIONS_PER_STEP=5
```

## Development

### Setup

1. Clone the repository:

```bash
git clone https://github.com/JovaniPink/mcp-browser-use.git
cd mcp-browser-use
```

2. Create and activate virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
uv sync
```

4. Start the server

```bash
uv run mcp-browser-use
```

### Debugging

For debugging, use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/project run mcp-server-browser-use
```

The Inspector will display a URL for the debugging interface.

## Browser Actions

The server supports various browser actions through natural language:

- Navigation: Go to URLs, back/forward, refresh
- Interaction: Click, type, scroll, hover
- Forms: Fill forms, submit, select options
- State: Get page content, take screenshots
- Tabs: Create, close, switch between tabs
- Vision: Find elements by visual appearance
- Cookies & Storage: Manage browser state

## Security

I want to note that their are some Chrome settings that are set to allow for the browser to be controlled by the server. This is a security risk and should be used with caution. The server is not intended to be used in a production environment.

Security Details: [SECURITY.MD](./documentation/SECURITY.md)

## Contributing

We welcome contributions to this project. Please follow these steps:

1. Fork this repository.
2. Create your feature branch: `git checkout -b my-new-feature`.
3. Commit your changes: `git commit -m 'Add some feature'`.
4. Push to the branch: `git push origin my-new-feature`.
5. Submit a pull request.

For major changes, open an issue first to discuss what you would like to change. Please update tests as appropriate to reflect any changes made.
