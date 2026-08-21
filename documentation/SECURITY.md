# Security boundary

This server gives an LLM control of a real browser. Treat every task and every
page as untrusted input, and treat a persistent browser profile as a credential.

## Defaults and architecture

- Each tool call creates its own `BrowserSession` and attempts graceful then
  forced cleanup.
- Task and context input is validated and bounded before provider or browser
  resources are allocated.
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

Do not enable `BROWSER_USE_DISABLE_SECURITY` for ordinary browsing. If a test
requires it, use a disposable browser with no authenticated profile and a
strict domain allowlist.

Proxying changes where traffic exits but is not a sandbox. Apply network policy
outside the process when destinations must be enforced independently of agent
instructions.

## Dependency integrity

Use the committed `uv.lock` with `--frozen` for installs, tests, and runtime
commands. A compatible environment (`uv pip check`) and a clean vulnerability
audit are separate requirements. The current browser-use 0.13.8 graph still
contains six advisories in three exactly pinned packages and has an upstream
security hold tracked in
[issue #45](https://github.com/JovaniPink/mcp-browser-use/issues/45); do not
allowlist findings or override browser-use's exact transitive pins. This branch
must remain unmerged until the issue's exact-head exit criteria pass.

## Reporting vulnerabilities

Open a private GitHub security advisory for vulnerabilities that could expose
credentials, browser sessions, or host resources. Use a normal issue for launch
or compatibility defects that contain no secrets.
