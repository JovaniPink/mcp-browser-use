# Security boundary

This server gives an LLM control of a real browser. Treat every task and every
page as untrusted input, and treat a persistent browser profile as a credential.

## Defaults and architecture

- Each tool call creates its own `BrowserSession`. Cleanup is shielded from
  AnyIO request cancellation; graceful stop has a 10-second deadline, with a
  5-second forced-stop fallback on failure or timeout. Native task cancellation
  is re-raised after the fallback rather than converted into success.
- Task and context input is validated and bounded before provider or browser
  resources are allocated.
- The active agent phase has a wall-clock limit (`MCP_RUN_TIMEOUT_SECONDS`).
  `MCP_MAX_CONCURRENT_RUNS` caps active requests, and a request retains its slot
  through its cleanup attempts. Shutdown failure is logged; these deadlines
  cannot guarantee process exit if both attempts fail or the server is killed
  externally. Operators still need process/container supervision.
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

Use the complete repository checkout and committed `uv.lock` with `--frozen`
for installation and runtime commands, or build the Docker image from that
checkout. The candidate selects an owned browser-use 0.13.14 wheel with build
tag `1mcbu1`; its packaging metadata permits the selected AnyIO 4.14.2,
FastMCP 4.2.6, MCP 2.3.0, browser-harness 0.1.15, Pillow 13.0.0, and pypdf
6.21.4 graph. Python 3.11.5 remains the minimum to exclude the older vulnerable
SoupSieve fallback.

The [provenance record](../compat/browser-use/provenance.json), source patch,
upstream archive and artifact hashes, MIT license, and
[verification/rebuild procedure](../compat/browser-use/README.md) accompany
the owned artifact. Its 182 browser-use runtime files are byte-identical to
the verified upstream source archive. Retaining the upstream distribution
name/version keeps it visible to advisory matching; the build tag and explicit
metadata identify the changed packaging. Verify the artifact before installing
it. Never silently substitute the published wheel, remove source verification,
or bypass the resolver's dependency checks.

`tool.uv.sources` is a repository installation contract and does not travel
inside the application wheel as normal dependency metadata. Ordinary
application-wheel installation against the published browser-use package does
not resolve this graph. Standalone wheel distribution, registry publication,
and deployment are outside this decision's supported scope.

Dependency compatibility, the unsuppressed audit, and runtime behavior are
separate gates. The [owned-build validation receipt](validation/owned-runtime-compatibility-2026-11-25.md)
records actual local results and the hosted checks still required. The
[earlier upstream-only audit](validation/runtime-follow-up-2026-11-25.md)
preserves the 77-record failure; it is not a result for the owned graph.

[Decision 0002](decisions/0002-owned-repository-compatibility-build.md) is
accepted for this bounded scope, effective only when PR #51 is merged after
the final published head passes the audit, supported Python matrix,
reproducible source build, MCP and real-browser boundaries, and non-root
container checks.
Until then, the release hold in
[decision 0001](decisions/0001-hold-unsafe-runtime-resolution.md) remains in
effect. A clean advisory scan is a point-in-time result, not proof of an
absence of defects; new advisories or failed compatibility checks reinstate
the hold. Do not allowlist findings, skip the owned package, or weaken gates.

External container images are pinned to manifest-list digests and GitHub
Actions to full commit SHAs. A dependency-free CI job enforces this, and
Renovate proposes digest refreshes for review.

## Reporting vulnerabilities

Open a private GitHub security advisory for vulnerabilities that could expose
credentials, browser sessions, or host resources. Use a normal issue for launch
or compatibility defects that contain no secrets.
