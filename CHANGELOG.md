# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

Release is on hold under
[decision 0001](documentation/decisions/0001-hold-unsafe-runtime-resolution.md)
until the exact runtime dependency audit passes without overrides.

### Changed

- Moved to browser-use 0.13.10's public `Agent`, `BrowserSession` and chat-model
  adapters, and to FastMCP 4. Removed the custom agent, controller and
  message-manager layer that imported private browser-use modules and made
  the server crash on launch (#8, #20).
- Installs, tests and the container build use the committed `uv.lock` with
  `--frozen`.
- The default model is `claude-opus-5`. `MCP_TEMPERATURE` is optional and
  unset by default, because current Anthropic models reject sampling
  parameters.
- The container runs Python 3.14 and Chromium as the unprivileged user 10001.

### Added

- `MCP_RUN_TIMEOUT_SECONDS` (default 600) sets a wall-clock limit per run.
  `MCP_MAX_CONCURRENT_RUNS` (default 1) caps how many browsers run at once.
- Task and context input is validated before any model or browser is allocated.
- CI covers Python 3.11–3.14, plus a separate mandatory runtime dependency
  audit, a container build and smoke test, and an immutable build-input
  contract.
- External container images are pinned to digests and GitHub Actions to commit
  SHAs. Renovate keeps both, and `uv.lock`, current through reviewed PRs.

### Security

- Credential-bearing CDP URLs are redacted, and proxy settings are left out of
  debug logs.
- The Smithery launcher maps only the selected provider's credential, and
  connects to CDP only when explicitly configured.
