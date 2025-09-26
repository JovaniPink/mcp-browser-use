# Configuration Guide

This guide describes every configuration option recognised by the MCP Browser Use server. All settings can be supplied as environment variables (e.g. via a `.env` file loaded with [`python-dotenv`](https://pypi.org/project/python-dotenv/)) or injected by your MCP client.

The sample file at [`sample.env.env`](../sample.env.env) contains a ready-to-copy template with placeholders for secrets.

## How configuration is loaded

1. **Model & Agent settings** are read in [`server.py`](../src/mcp_browser_use/server.py). They control the language model as well as the agent run loop.
2. **Browser runtime settings** are parsed in [`browser/browser_manager.py`](../src/mcp_browser_use/browser/browser_manager.py) which returns a configured `BrowserSession` instance.
3. **Provider specific credentials** are consumed by the LLM factory in [`utils/utils.py`](../src/mcp_browser_use/utils/utils.py).

Unless otherwise noted, boolean flags treat any of `1`, `true`, `yes`, `on` (case insensitive) as **true**. Any other value is considered **false**.

## Core Agent Options

| Variable | Default | Description |
| --- | --- | --- |
| `MCP_MODEL_PROVIDER` | `anthropic` | LLM provider name passed to the LangChain factory. Supported values: `anthropic`, `openai`, `deepseek`, `gemini`, `ollama`, `azure_openai`. |
| `MCP_MODEL_NAME` | `claude-3-5-sonnet-20241022` | Model identifier sent to the provider. Each provider supports its own model list. |
| `MCP_TEMPERATURE` | `0.3` | Sampling temperature for the model. Parsed as float. |
| `MCP_MAX_STEPS` | `30` | Maximum number of reasoning/action steps before aborting the run. Parsed as integer. |
| `MCP_MAX_ACTIONS_PER_STEP` | `5` | Limits how many tool invocations the agent may issue in a single step. Parsed as integer. |
| `MCP_USE_VISION` | `true` | Enables vision features within the agent (element snapshots). |
| `MCP_TOOL_CALL_IN_CONTENT` | `true` | Whether tool call payloads are expected inside the model response content. |

## Provider Credentials & Endpoints

The LLM factory reads the following variables when initialising clients. Only set the values for the provider(s) you actively use.

| Variable | Purpose |
| --- | --- |
| `ANTHROPIC_API_KEY` | API key for Anthropic Claude models. |
| `OPENAI_API_KEY` | API key for OpenAI models. |
| `DEEPSEEK_API_KEY` | API key for DeepSeek hosted models. |
| `GOOGLE_API_KEY` | API key for Google Gemini via LangChain Google Generative AI. |
| `AZURE_OPENAI_API_KEY` | API key for Azure OpenAI deployments. |
| `AZURE_OPENAI_ENDPOINT` | Endpoint URL for the Azure OpenAI deployment. |
| `OPENAI_ENDPOINT` | Override the OpenAI base URL (useful for proxies). |
| `DEEPSEEK_ENDPOINT` | Base URL for the DeepSeek-compatible endpoint. |
| `ANTHROPIC_API_ENDPOINT` | Alternative base URL for Anthropic (rarely needed). |

When pointing to self-hosted or compatible services you may also override the defaults using `base_url` specific variables in your own code. See [`utils/utils.py`](../src/mcp_browser_use/utils/utils.py) for the full mapping.

## Browser Runtime Options

These options are parsed by [`BrowserEnvironmentConfig.from_env`](../src/mcp_browser_use/browser/browser_manager.py) and control Chromium launch behaviour.

| Variable | Default | Description |
| --- | --- | --- |
| `CHROME_PATH` | _unset_ | Absolute path to a Chrome/Chromium executable. Leave unset to let `browser-use` manage Chromium via Playwright. |
| `CHROME_USER_DATA` | _unset_ | Directory to store user data (profiles, cookies). Required when `CHROME_PERSISTENT_SESSION` is true. |
| `CHROME_PERSISTENT_SESSION` | `false` | Keeps the browser profile between runs by mounting `CHROME_USER_DATA`. |
| `CHROME_DEBUGGING_PORT` | _unset_ | Remote debugging port for attaching to an existing Chrome instance. Must be an integer. |
| `CHROME_DEBUGGING_HOST` | _unset_ | Hostname/IP for remote debugging (e.g. `localhost`). |
| `BROWSER_USE_HEADLESS` | `false` | Launch Chromium in headless mode. |
| `BROWSER_USE_DISABLE_SECURITY` | `false` | Disables web security features (CORS, sandbox). Use with caution. |
| `BROWSER_USE_EXTRA_CHROMIUM_ARGS` | _unset_ | Comma-separated list of additional Chromium command-line flags. |
| `BROWSER_USE_ALLOWED_DOMAINS` | _unset_ | Comma-separated allowlist limiting which domains the agent may open. |
| `BROWSER_USE_PROXY_URL` | _unset_ | HTTP/HTTPS proxy URL. |
| `BROWSER_USE_NO_PROXY` | _unset_ | Hosts to bypass in proxy mode. |
| `BROWSER_USE_PROXY_USERNAME` | _unset_ | Username for proxy authentication. |
| `BROWSER_USE_PROXY_PASSWORD` | _unset_ | Password for proxy authentication. |
| `BROWSER_USE_CDP_URL` | _unset_ | Connect to an existing Chrome DevTools Protocol endpoint instead of launching a new browser. |

### Persistence hints

- When `CHROME_PERSISTENT_SESSION` is true and `CHROME_USER_DATA` is not provided, the server logs a warning and the session falls back to ephemeral storage.
- Remote debugging settings (`CHROME_DEBUGGING_HOST` / `CHROME_DEBUGGING_PORT`) are optional and ignored if invalid values are supplied. The server logs a warning and continues with defaults.

## Additional Environment Variables

Some ancillary features inspect the following variables:

| Variable | Purpose |
| --- | --- |
| `WIN_FONT_DIR` | Custom Windows font directory used when generating GIF summaries of browsing sessions. |
| `BROWSER_USE_EXTRA_CHROMIUM_ARGS` | Recognised both by the browser manager and various tests to tweak launch flags. |

## Tips for managing configuration

- Store secrets outside of version control. When sharing an `.env` file, redact or rotate keys immediately.
- Keep provider-specific settings grouped so you can switch model providers quickly when testing.
- Start with the defaults, confirm the agent behaves as expected, then tighten security by restricting `BROWSER_USE_ALLOWED_DOMAINS` and enabling headless mode.
- When experimenting locally, keep `CHROME_PERSISTENT_SESSION=false` to avoid stale cookies interfering with automation runs.

For any options not covered here, consult the upstream [`browser-use` documentation](https://github.com/browser-use/browser-use) which explains additional environment variables recognised by the underlying library.
