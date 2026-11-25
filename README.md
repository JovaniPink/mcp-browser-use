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

- Python 3.11.5 or newer in the supported 3.11 through 3.14 series
- [`uv`](https://docs.astral.sh/uv/) 0.12.3 for the documented frozen build
- Chrome/Chromium, unless connecting through `BROWSER_USE_CDP_URL`
- an API key for the selected hosted model provider (Ollama is keyless)

The production container includes Chromium and runs the MCP process as UID
10001. It defaults to headless browsing.

## Install and run

```sh
git clone https://github.com/JovaniPink/mcp-browser-use.git
cd mcp-browser-use
cp .env.example .env
python3 compat/browser-use/verify.py
uv sync --frozen
uv run --frozen --env-file .env mcp-browser-use
```

Keep the complete checkout, including `compat/browser-use/`. This candidate
uses a repository-owned browser-use packaging build selected by
`tool.uv.sources` and `uv.lock`. The supported delivery paths are this frozen
checkout and its Docker build. Installing the application wheel alone or
publishing it to a registry does not reproduce that dependency selection and
is not supported by this compatibility decision.

The console command starts FastMCP over stdio. Configure it as a child process
of your MCP client; do not start it separately and then point the client at a
TCP port.

The server does not load `.env` itself. The command above loads it explicitly;
the client configuration below instead injects environment values directly.

The included `smithery.yaml` uses the same frozen command and provider contract.
It requires one provider-neutral API key for every hosted provider and maps that
key to only the selected provider. Ollama is the sole keyless option. The schema
uses Smithery's documented [JSON Schema configuration
contract](https://smithery.ai/docs/build/session-config) and JSON Schema
[`if`/`then` conditional
validation](https://json-schema.org/understanding-json-schema/reference/conditionals)
to require the key. The command function repeats the check before returning a
process command, so a keyless hosted-provider session fails closed even if a
client does not surface the conditional field guidance. Smithery does not assume
a CDP port; provide an explicit authenticated CDP URL only when attaching to an
existing browser is intentional.

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
        "MCP_MODEL_NAME": "claude-opus-5",
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
`MCP_MAX_ACTIONS_PER_STEP` to 1–20. Each run is cut off after
`MCP_RUN_TIMEOUT_SECONDS` (default 600), and at most `MCP_MAX_CONCURRENT_RUNS`
runs (default 1) hold a browser at once; later requests wait for a free slot.
The run slot remains occupied while cleanup attempts finish. Cleanup is
shielded from request cancellation, with separate graceful-stop and forced-stop
deadlines, and the original cancellation is preserved. Failed shutdown attempts
are logged; a process may remain if both attempts fail or the server is killed
externally. See the [security boundary](documentation/SECURITY.md).

## Development and validation

```sh
python3.14 -m pip install uv==0.12.3
python3 compat/browser-use/verify.py
python3 compat/browser-use/build.py --check
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

CI is configured to run the functional gates on Python 3.11, 3.12, 3.13, and
3.14, reproduce the owned artifact, and build both Docker targets. The runtime
container must pass browser/document and MCP subprocess probes as UID 10001
with networking disabled. A separate required job exports the exact runtime
graph and runs an unsuppressed `pip-audit`, including the owned distribution.
These gates remain necessary on the final published head; the
[validation receipt](documentation/validation/owned-runtime-compatibility-2026-11-25.md)
separates local results from pending hosted checks.

### Dependency release boundary

The current candidate uses the owned
`browser_use-0.13.14-1mcbu1-py3-none-any.whl`, FastMCP 4.2.6, AnyIO 4.14.2,
MCP 2.3.0, browser-harness 0.1.15, Pillow 13.0.0, and pypdf 6.21.4. Its actual
wheel metadata declares the changed requirements, so the ordinary resolver and
dependency checks still apply. Python 3.11.5 remains the minimum to exclude the
older vulnerable SoupSieve fallback.

The owned build changes packaging metadata; its 182 browser-use runtime files
match the verified upstream source archive. It preserves the upstream MIT
license and the `browser-use` name/version used by advisory matching. The build
tag, explicit summary, source patch, archive and artifact hashes, and
[verification/rebuild procedure](compat/browser-use/README.md) distinguish it
from the published distribution. No advisory is allowlisted or skipped.

[Decision 0002](documentation/decisions/0002-owned-repository-compatibility-build.md)
records the accepted bounded checkout/container delivery contract. It takes
effect only when PR #51 is merged after its mandatory checks pass, including
compatibility, audit, matrix, source-build, and container gates. Local results
do not establish completed adoption or qualify a release. The
[earlier decision](documentation/decisions/0001-hold-unsafe-runtime-resolution.md)
and [upstream-only audit](documentation/validation/runtime-follow-up-2026-11-25.md)
remain historical evidence. No standalone application-wheel publication,
registry upload, or deployment is included.

A dependency-free CI job also enforces that external container images use
digests and GitHub Actions use full commit SHAs. Renovate proposes refreshes of
those pins and of `uv.lock` for review.

## Docker

```sh
docker build --target test -t mcp-browser-use:test .
docker run --rm mcp-browser-use:test
docker build -t mcp-browser-use:local .
docker run --rm -i --env-file .env mcp-browser-use:local
```

The Docker context excludes local virtual environments, Git metadata, `.env`
files and build caches; pass provider secrets only at runtime.

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
dependency migration remains unreleased until all checks on the final head and
the reviewed integration pass; do not suppress the audit or bypass dependency
metadata to make it pass.

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
