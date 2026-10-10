# Security boundary

This server gives an LLM control of a real browser. Treat every task and every
page as untrusted input, and treat a persistent browser profile as a credential.

## Defaults and architecture

- Each tool call creates its own `BrowserSession` and attempts graceful then
  forced cleanup.
- Task and context input is validated and bounded before provider or browser
  resources are allocated.
- Each run has a wall-clock limit (`MCP_RUN_TIMEOUT_SECONDS`) and the number of
  simultaneous browsers is capped (`MCP_MAX_CONCURRENT_RUNS`), so a stuck page
  or a burst of calls cannot hold or spawn Chromium processes without bound.
- Browser security remains enabled unless
  `BROWSER_USE_DISABLE_SECURITY=true` is explicitly set.
- Model adapters and agent orchestration use browser-use's public API; this
  repository does not import private telemetry or message-manager internals.
- The old host clipboard tools were removed so an agent cannot read or overwrite
  the user's OS clipboard through this server.
- The container runs as UID 10001 and uses an ephemeral browser profile unless
  the operator mounts one intentionally.

## Operator responsibilities

1. Restrict navigation with `BROWSER_USE_ALLOWED_DOMAINS` whenever the task has
   a known destination set.
2. Use ephemeral profiles for untrusted tasks. A persisted profile may contain
   cookies, authentication sessions, saved form data, and browsing history.
3. Keep provider keys in a secret manager or MCP client secret store. Never log
   full environment dictionaries. Credential-bearing CDP URLs are redacted from
   the server's debug output.
4. Run the server in an isolated container or VM when tasks may download files
   or visit unknown pages.
5. Keep CDP endpoints bound to localhost or behind an authenticated tunnel. An
   exposed CDP endpoint grants full browser control.
6. Review tasks that can submit forms, purchase items, publish content, or alter
   external systems. The MCP tool does not add a human-approval workflow.

## Network and browser controls

Do not enable `BROWSER_USE_DISABLE_SECURITY` for ordinary browsing. It turns
off browser protections such as the same-origin policy, so any page the agent
visits can read data from any other origin in that browser. If a test requires
it, use a disposable browser with no authenticated profile and a strict domain
allowlist.

Proxying changes where traffic exits but is not a sandbox. Apply network policy
outside the process when destinations must be enforced independently of agent
instructions.

## Dependency integrity

Use the committed `uv.lock` with `--frozen` for installs, tests, and runtime
commands. A compatible environment (`uv pip check`) and a clean vulnerability
audit are separate requirements. The candidate pairs browser-use 0.13.10 with
FastMCP 4.0.3, which admits patched Click, MCP 2 and pypdf without overrides.
Its runtime audit passed on 2026-09-06. On 2026-09-26 it reported two new
advisories in anyio 4.12.1 (CVE-2026-63374, CVE-2026-64847; fixed in 4.14.2),
which browser-use 0.13.10 pins exactly. The release stays on hold under
[decision 0001](decisions/0001-hold-unsafe-runtime-resolution.md) and
[issue #45](https://github.com/JovaniPink/mcp-browser-use/issues/45) until
upstream publishes compatible metadata. A clean audit is a point-in-time result:
CI re-runs it on every change, and new advisories can turn it red without a code
change. Do not allowlist findings or override upstream exact transitive pins.

External container images are pinned to manifest-list digests and GitHub
Actions to full commit SHAs. A dependency-free CI job enforces this, and
Renovate proposes digest refreshes for review.

## Reporting vulnerabilities

Open a private GitHub security advisory for vulnerabilities that could expose
credentials, browser sessions, or host resources. Use a normal issue for launch
or compatibility defects that contain no secrets.
