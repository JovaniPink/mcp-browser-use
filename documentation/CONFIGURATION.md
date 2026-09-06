# Configuration

Settings are read for each `run_browser_agent` call, so model and limit changes
do not require restarting a long-lived Python process. Load `.env` through your
MCP client, shell, container runtime, or another secret-injection mechanism.

## Agent settings

| Variable | Default | Contract |
| --- | --- | --- |
| `MCP_MODEL_PROVIDER` | `anthropic` | One of `anthropic`, `azure_openai`, `browser_use`, `deepseek`, `gemini`, `ollama`, or `openai`. |
| `MCP_MODEL_NAME` | `claude-sonnet-4-6` | Provider-specific model identifier. |
| `MCP_TEMPERATURE` | `0.3` | Float passed to providers that support temperature. |
| `MCP_MAX_STEPS` | `30` | Integer clamped to 1–100. |
| `MCP_MAX_ACTIONS_PER_STEP` | `5` | Integer clamped to 1–20. |
| `MCP_USE_VISION` | `true` | `1`, `true`, `yes`, or `on` enables screenshots. |

Invalid numeric values fall back to their documented defaults and emit a
warning without logging secrets.

## Tool input contract

`run_browser_agent` trims its `task` and optional `add_infos` values before use.
The task must be non-empty, and each input is limited to 20,000 characters.
Validation happens before model or browser-session allocation so malformed or
oversized requests do not consume provider or browser resources.

## Provider credentials

| Provider | Required values | Optional endpoint values |
| --- | --- | --- |
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_API_ENDPOINT` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` | `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION` |
| Browser Use | `BROWSER_USE_API_KEY` | none |
| DeepSeek | `DEEPSEEK_API_KEY` | `DEEPSEEK_ENDPOINT` |
| Gemini | `GOOGLE_API_KEY` | none |
| Ollama | a reachable local/remote Ollama service | `OLLAMA_HOST` |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_ENDPOINT` |

Only configure the selected provider. Never place real values in
`.env.example`, repository files, issue comments, or debug logs.

## Browser settings

| Variable | Default | Contract |
| --- | --- | --- |
| `BROWSER_USE_HEADLESS` | `false` locally | Launch without a visible window. The container sets this to `true`. |
| `BROWSER_USE_DISABLE_SECURITY` | `false` | Disables browser security only when explicitly true. Avoid for untrusted pages. |
| `BROWSER_USE_ALLOWED_DOMAINS` | unset | Comma-separated navigation allowlist. |
| `BROWSER_USE_EXTRA_CHROMIUM_ARGS` | unset | Comma-separated extra Chromium arguments. |
| `BROWSER_USE_CDP_URL` | unset | Attach to an existing CDP endpoint instead of launching Chromium. |
| `CHROME_PATH` | unset locally | Explicit Chrome/Chromium executable. The container uses `/usr/bin/chromium`. |

## Persistence and debugging

| Variable | Default | Contract |
| --- | --- | --- |
| `CHROME_PERSISTENT_SESSION` | `false` | Reuse `CHROME_USER_DATA` across runs. |
| `CHROME_USER_DATA` | unset | Profile directory used only when persistence is enabled. |
| `CHROME_DEBUGGING_HOST` | `127.0.0.1` when derived | Host used with `CHROME_DEBUGGING_PORT`. |
| `CHROME_DEBUGGING_PORT` | unset | Integer used to derive a CDP URL when `BROWSER_USE_CDP_URL` is absent. |

Prefer the explicit `BROWSER_USE_CDP_URL`. Never expose an unauthenticated CDP
endpoint to the public internet; it provides full browser control.

## Proxy settings

- `BROWSER_USE_PROXY_URL`
- `BROWSER_USE_NO_PROXY`
- `BROWSER_USE_PROXY_USERNAME`
- `BROWSER_USE_PROXY_PASSWORD`

Proxy credentials are passed to browser-use's `ProxySettings` object and are
excluded from debug output. CDP URLs are also redacted because their user-info
or query parameters may contain access tokens.
