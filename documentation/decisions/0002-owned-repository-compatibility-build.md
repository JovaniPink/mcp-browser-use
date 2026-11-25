# Decision 0002: Use an owned compatibility build for frozen repository installs

- **Status:** Accepted for the stated scope; effective only when PR #51 is merged after its mandatory checks pass
- **Date:** 2026-11-25
- **Scope:** The documented frozen repository checkout and Docker runtime
- **Predecessor:** [Decision 0001](0001-hold-unsafe-runtime-resolution.md), whose historical evidence remains intact
- **Tracking:** [#8](https://github.com/JovaniPink/mcp-browser-use/issues/8), [#45](https://github.com/JovaniPink/mcp-browser-use/issues/45), [#49](https://github.com/JovaniPink/mcp-browser-use/issues/49), and [#51](https://github.com/JovaniPink/mcp-browser-use/pull/51)

## Problem and choice

Published browser-use 0.13.14 requires dependency versions that fail the
runtime audit. Its exact requirements also prevent selection of the published
browser-harness 0.1.15 and patched FastMCP/MCP combination. The inspected 1.x
alternative changes public APIs used by this server and retains an affected
Pillow requirement. An ordinary upstream-only refresh does not satisfy the
current compatibility and audit gates.

For the repository and container, use a small, repository-contained packaging
patch to browser-use 0.13.14. The owned wheel has build tag `1mcbu1`, keeps the
upstream package name and source version for advisory matching, and preserves
the upstream MIT license. All 182 browser-use runtime files match the verified
upstream source archive. The patch changes declared dependency requirements;
it does not replace browser-use runtime code or force the installer to ignore
requirements.

The selected graph uses AnyIO 4.14.2, FastMCP 4.2.6, MCP 2.3.0,
browser-harness 0.1.15, Pillow 13.0.0, and pypdf 6.21.4. It is resolved from the
actual rebuilt wheel's metadata and committed in `uv.lock`.

## Supported delivery boundary

The supported paths are the documented checkout installed with
`uv sync --frozen` and the Docker build that consumes that same lock and owned
artifact. The wheel, source patch, upstream archive hash, license, artifact
hash, and verification/rebuild procedure live together under
`compat/browser-use/`. Docker must verify and copy the artifact before its
dependency installation layer.

The application wheel alone does not carry `tool.uv.sources`. Installing it
against the published browser-use distribution therefore does not reproduce
this graph. The normal wheel-only resolver probe fails first on the
application's AnyIO 4.14.2 requirement versus published browser-use's exact
4.12.1 requirement; the selected FastMCP and published browser-use MCP
requirements also conflict. Standalone application-wheel and registry publication
remain unsupported by this decision. No package release, registry upload,
new upstream fork repository, or deployment is included.

## Acceptance evidence

The decision takes effect only after the same published candidate passes:

- Frozen installation, dependency consistency, and an unsuppressed runtime
  audit that includes the owned browser-use distribution and skips none.
- The full supported Python matrix and existing immutable-input checks.
- Source/artifact verification and a reproducible build of the owned wheel.
- MCP startup, initialization, tool discovery, cancellation, disconnect,
  cleanup, and subsequent-request behavior using actual subprocesses.
- Local Chromium navigation and screenshot behavior, AnyIO-backed screenshot
  storage, Pillow resizing, and PDF reads through the installed dependencies.
- The production container build and smoke checks as its non-root runtime user.

The [validation receipt](../validation/owned-runtime-compatibility-2026-11-25.md)
and PR #51 record the executed commands, exact inputs, results, and remaining
limits. Hosted checks for the final candidate are pending at this decision's
preparation; earlier passing runs do not satisfy this condition. Reviewed
integration is still required. A clean advisory scan is evidence about the
queried feed and selected graph, not proof that the application has no defects.
No paid provider journey or harness daemon/IPC qualification is inferred from
offline browser and helper tests. The runtime browser probes must run without
provider calls or external navigation, using local fixtures and the real
Chromium binary as UID 10001; component tests cannot substitute for them.

The server cleanup repair must preserve the original cancellation, retain the
run slot until bounded cleanup attempts finish, and report shutdown failures.
Bounded graceful and forced attempts do not guarantee process termination if
both attempts fail or the server is forcibly killed externally.

## Maintenance and replacement

This repository owns the checked-in packaging patch and its integration
contract. Every update must preserve the source and artifact provenance,
license, advisory identity, ordinary dependency resolution, and required
behavioral/audit gates. Do not silently replace the owned build with a registry
wheel that has different requirements, and do not suppress advisories to keep
the candidate green.

Prefer returning to an upstream-only graph when a published browser-use
release permits patched dependencies and passes the same compatibility
checks. Remove the owned artifact and its source mapping together in that
reviewed change. A new audit or compatibility failure reinstates the
integration hold; it does not authorize a downgrade to a known-unsafe graph.

This decision defines the bounded repository delivery and review contract. It
does not make a staffing, spending, release-timing, or external support promise.
