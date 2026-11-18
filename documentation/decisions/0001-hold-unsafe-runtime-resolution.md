# Decision 0001: Hold the unsafe runtime resolution

- **Status:** Active hold
- **Decided:** 2026-08-16
- **Last verified:** 2026-11-17
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

## 2026-09-05 candidate follow-through

The 0.13.8 frozen head now reports ten advisories across the same three packages.
Current [browser-use metadata](https://pypi.org/pypi/browser-use/0.13.10/json)
permits patched versions but requires MCP 2, outside FastMCP 3.4.6's range.
The compatible candidate therefore pairs browser-use 0.13.10 with FastMCP 4.0.3,
following the [FastMCP migration guide](https://gofastmcp.com/getting-started/upgrading/from-fastmcp-3).
Local Python 3.14 tests, automatic/legacy protocol exchanges, dependency
compatibility and the runtime audit pass without overrides or suppressions.
This does not reverse the release hold: complete matrix, container and hosted
checks on the committed candidate remain necessary, as does separate merge
authorization. This note supplements the historical evidence above.

## 2026-09-26 status update

Hosted checks on PR #47 head `0e9545a` (browser-use 0.13.10, FastMCP 4.0.3)
all passed on 2026-09-06, including the runtime audit. The Click, MCP and pypdf
blocker is resolved.

Re-running the same exact audit on 2026-09-26 reports two new advisories in
anyio 4.12.1 (CVE-2026-63374 and CVE-2026-64847, fixed in 4.14.2).
browser-use 0.13.10 is still the latest release and pins `anyio==4.12.1`
exactly, so `uv lock --upgrade-package anyio` cannot move it. This is the same
kind of blocker, now in a different package, and the hold stays active. The
owner re-confirmed that it should not be lifted with an override or
suppression.

The work from PR #47 and the digest pinning from PR #48 are now combined on one
branch. PR #48 is superseded, because its digests were for the previous base
images. Once a browser-use release permits anyio 4.14.2 or later, lifting the
hold takes one step: refresh the lock, then re-run the existing gates on that
exact head. The reversal criteria above are unchanged.

## 2026-11-17 compatible repair and refreshed evidence

The earlier two-advisory status is historical. A fresh unsuppressed audit of
the selected PR #51 lock reports 140 advisory records across 17 packages.
The compatible browser-use 0.13.14 update and targeted lock refresh reduce
that to 76 records across five packages. Unrelated locked versions are
preserved. Python >=3.11.5 excludes an unsafe SoupSieve fallback selected by
earlier Python 3.11 patches.

The repository-owned Ollama temperature mapping and reusable-workflow pin
detection defects are repaired with regressions that failed before the fixes.
These repairs do not reverse the dependency hold.

The current upstream constraints still require AnyIO 4.12.1, MCP 2.1.1,
Pillow 12.3.0, and pypdf 6.16.2. A normal resolver rejects patched FastMCP 4.1.2
because it requires MCP >=2.2.0. Browser-use 1.0.6 both changes the runtime
contract materially and still pins the affected Pillow version, so it is not
adopted as a security shortcut.

A metadata-only feasibility probe also showed that changing the four
browser-use pins alone is insufficient: its browser-harness 0.1.13 dependency
independently pins Pillow 12.3.0. A maintained compatibility fork would need
to address both packages and test their behavioral differences. No such fork
has been adopted or authorized by this update.

The [validation record](../validation/runtime-repair-2026-11-17.md) identifies
the exact manifest and lock, remaining packages, commands, and evidence
limits. The existing reversal criteria and separate merge authorization
remain in force; no advisory suppression or resolver override was introduced.
