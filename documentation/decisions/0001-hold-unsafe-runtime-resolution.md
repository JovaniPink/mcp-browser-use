# Decision 0001: Hold the unsafe runtime resolution

- **Status:** Active hold
- **Decided:** 2026-08-16
- **Last verified:** 2026-08-21
- **Issues:** [#45](https://github.com/JovaniPink/mcp-browser-use/issues/45), [#49](https://github.com/JovaniPink/mcp-browser-use/issues/49)

## Context

The proposed Python 3.14 and `browser-use` modernization in
[PR #47](https://github.com/JovaniPink/mcp-browser-use/pull/47) passes its
ordinary Python and container checks, but its exact resolved runtime dependency
audit fails. The upstream `browser-use` release constrains vulnerable transitive
packages. Forcing replacements outside upstream metadata would create an
unreviewed compatibility fork while leaving the audit result misleading.

Separately, main has no committed `uv.lock` even though the Dockerfile mounts it
during the build. [PR #48](https://github.com/JovaniPink/mcp-browser-use/pull/48)
pins container images, but merging it alone would not establish a reproducible,
audited application environment.

## Decision

- Do not merge PR #47 while the exact runtime dependency audit fails.
- Do not suppress advisories or force transitive versions that violate upstream
  package metadata.
- Do not generate and bless a container lock from the known-unsafe graph merely
  to make the Dockerfile reproducible.
- Keep immutable container-image work separate until it can be validated with a
  safe application lock and complete container build.

This is a release hold, not a conclusion that every upstream advisory is
exploitable through this server.

On 2026-08-21, `browser-use` 0.13.8 reduced the exact runtime audit from 53
advisories in five packages to six advisories in three packages by updating
aiohttp and Pillow. Its metadata still pins Click 8.3.1, MCP 1.26.0, and pypdf
6.14.2 below their audited fixes, so the hold remains active.

## Consequences

- The modernization and image-pin pull requests remain unmerged.
- Main's container path is not release-ready until the missing-lock contract is
  repaired.
- Operators should continue to isolate browser automation and follow
  [`../SECURITY.md`](../SECURITY.md); isolation reduces exposure but does not
  replace dependency remediation.

## Reversal criteria

Reconsider this hold only when one of these paths is reviewed:

1. an upstream release permits a patched dependency graph; or
2. the owner explicitly authorizes a compatibility fork or override and its
   behavioral differences are tested and maintained.

The resulting exact head must then provide a committed reproducible lock, clean
dependency conflict and vulnerability checks, the full Python matrix, a
container build and smoke test using that lock, and current MCP/browser boundary
tests. Record the replacement decision instead of rewriting this history.
