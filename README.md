# MCP Browser Use Server

An MCP server that exposes browser automation through the maintained public API
of [`browser-use`](https://github.com/browser-use/browser-use). It provides one
tool, `run_browser_agent`, for running a natural-language browser task in a
fresh, isolated browser session.

## Architecture

```text
MCP client
  -> FastMCP stdio server
  -> validated per-run configuration
  -> browser-use Agent + native provider adapter
  -> isolated BrowserSession
  -> Chromium or an explicit CDP endpoint
```

The server deliberately does not subclass browser-use's private agent,
telemetry, prompt, or message-manager internals. Provider adapters come directly
from browser-use, which keeps the MCP boundary stable when upstream internals
change. Each request owns its browser session and always attempts cleanup.

## Requirements

- Python 3.11 through 3.14
- [`uv`](https://docs.astral.sh/uv/) 0.12.3 or newer
- Chrome/Chromium, unless connecting through `BROWSER_USE_CDP_URL`
- an API key for the selected model provider

The production container includes Chromium and runs the MCP process as UID
10001. It defaults to headless browsing.

## Install and run

```sh
git clone https://github.com/JovaniPink/mcp-browser-use.git
cd mcp-browser-use
cp .env.example .env
uv sync --frozen
uv run mcp-browser-use
```

The console command starts FastMCP over stdio. Configure it as a child process
of your MCP client; do not start it separately and then point the client at a
TCP port.

Example client configuration:

```json
{
  "mcpServers": {
    "browser-use": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-browser-use",
        "run",
        "--frozen",
        "mcp-browser-use"
      ],
      "env": {
        "MCP_MODEL_PROVIDER": "anthropic",
        "MCP_MODEL_NAME": "claude-sonnet-4-6",
        "ANTHROPIC_API_KEY": "replace-in-your-client-secret-store"
      }
    }
  }
}
```

Use an absolute repository path. Keep credentials in the MCP client's secret
store rather than committing them to its JSON configuration.

## Configuration

Copy [`.env.example`](./.env.example) for the supported variables and read the
[configuration guide](./documentation/CONFIGURATION.md) for provider, browser,
proxy, persistence, and limit behavior.

Supported provider values are:

- `anthropic`
- `azure_openai`
- `browser_use`
- `deepseek`
- `gemini`
- `ollama`
- `openai`

The server validates tool input before allocating a model or browser session. It
rejects an empty task, limits both the task and optional context to 20,000
characters each, bounds `MCP_MAX_STEPS` to 1–100, and bounds
`MCP_MAX_ACTIONS_PER_STEP` to 1–20.

## Development and validation

```sh
python3.14 -m pip install uv==0.12.3
uv sync --frozen --dev
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen pytest -q
uv pip check
uv export --frozen --no-dev --no-emit-project \
  --format requirements-txt --output-file /tmp/mcp-browser-use-requirements.txt
uvx --from pip-audit==2.10.1 pip-audit \
  -r /tmp/mcp-browser-use-requirements.txt
```

CI runs those gates on Python 3.12 and 3.14, then builds both Docker targets and
verifies the runtime image can import the server and execute Chromium.

### Dependency release boundary

The public-API migration fixes fresh-install launch failures, but it is not
merge-ready while [issue #45](https://github.com/JovaniPink/mcp-browser-use/issues/45)
remains open. `browser-use==0.13.7` currently hard-pins vulnerable versions of
aiohttp, Click, MCP, Pillow, and pypdf. The exact exported runtime graph reports
53 advisories. Do not suppress those findings, force incompatible transitive
overrides, or treat passing imports and tests as a substitute for the audit.

Merge only after browser-use publishes compatible metadata, `uv.lock` is
refreshed without overrides, `uv pip check` passes, and the exact `pip-audit`,
Python matrix, and container gates are green on the same head.

## Docker

```sh
docker build --target test -t mcp-browser-use:test .
docker run --rm mcp-browser-use:test
docker build -t mcp-browser-use:local .
docker run --rm -i --env-file .env mcp-browser-use:local
```

The MCP protocol uses stdin/stdout, so keep `-i`. Browser sessions are ephemeral
unless you explicitly mount a profile and enable persistence.

## Security boundary

Browser automation can read pages, enter data, download files, and act with the
permissions of a persisted browser profile. Use allowed-domain restrictions,
ephemeral profiles, least-privilege credentials, and an isolated container or
VM for untrusted tasks. The OS clipboard actions from the older implementation
were removed. See [SECURITY.md](./documentation/SECURITY.md).

The complete documentation map and active dependency decision record are in
[documentation/README.md](documentation/README.md). The Python 3.14/browser-use
dependency migration remains held until upstream permits a clean production
resolution; do not suppress the audit or force incompatible transitive versions.

## Troubleshooting

- `ImportError` mentioning browser-use telemetry or agent internals means an old
  checkout or environment is still installed. Run `uv sync --frozen --refresh`
  from a current checkout.
- If the MCP client cannot launch the command, use absolute paths and confirm
  `uv run --frozen mcp-browser-use` starts without an import traceback.
- If Chromium cannot start, set `CHROME_PATH` or use the provided container.
- If connecting to an existing browser, set only `BROWSER_USE_CDP_URL`; do not
  expose a debugging port publicly.

## Contributing

Keep changes on public browser-use and FastMCP APIs. Update `uv.lock`, tests,
the relevant documentation, and the Docker/import smoke gates in the same PR.

## License

MIT. See [LICENSE](./LICENSE).
