# Runtime dependency follow-up — November 25, 2026

## Result

The supported runtime remains blocked. A fresh, unsuppressed audit of the
unchanged PR #51 runtime reports **77 advisory records across five packages**,
one more MCP record than the November 17 receipt. Normal resolver attempts
reject both a patched FastMCP upgrade and the newly published browser-harness
upgrade. The latest browser-use major release still pins affected Pillow and
changes this server's public API contract.

This follow-up repairs the stale evidence and integration status; it does not
claim a runtime security fix. PR #51 remains the single draft candidate and
[decision 0001](../decisions/0001-hold-unsafe-runtime-resolution.md) remains active.
No override, advisory suppression, fork, or change to the security gates was
introduced. Runtime source, `pyproject.toml`, and `uv.lock` are unchanged from
`a0063336759745c0e5b29c461f0ac57b1c482e8c`.

## Fresh audit

The [machine-readable receipt](runtime-audit-2026-11-25.json) includes input
hashes, all advisory identifiers, exact upstream metadata, resolver failures,
and the inspected upstream wheel's verified hash. The audit used the frozen
runtime-only export, CPython 3.14.7, uv 0.12.3, and pip-audit 2.10.1. It checked
136 distributions with zero skipped entries and exited 1.

| Package | Locked version | Advisory records | Highest recorded fixed floor on the selected line |
| --- | --- | ---: | --- |
| AnyIO | 4.12.1 | 2 | 4.14.2 |
| FastMCP | 4.0.3 | 2 | 4.1.2 |
| MCP | 2.1.1 | 5 | 2.2.0 |
| Pillow | 12.3.0 | 42 | 13.0.0 |
| pypdf | 6.16.2 | 26 | 6.21.4 |

The additional record is CVE-2026-115563 / GHSA-qx49-fqc8-xw99. The
[upstream advisory](https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-qx49-fqc8-xw99)
concerns OAuth-enabled HTTP clients and expressly excludes SDK servers and
stdio clients. That limits its relevance to this server; it does not justify
silently dropping the record or claiming the complete graph is clean. The
advisory was published before this follow-up: “additional” refers to the audit
comparison, not its publication date.

These counts describe audit records, not independent application defects or
proof that every affected feature is exercised here.

## Published upgrade paths actually checked

As checked on November 25, browser-use 0.13.14 remains the newest 0.x release.
It requires `anyio==4.12.1`, `mcp==2.1.1`, `pillow==12.3.0`,
`pypdf==6.16.2`, and `browser-harness==0.1.13`.

There is material upstream progress: **browser-harness 0.1.15**, published on
November 25, requires **Pillow 13.0.0** in its default dependencies. This
supersedes November 17's claim that the latest published harness itself must
be forked to permit Pillow 13. Its optional `mcp` extra still pins MCP 2.1.1;
the current browser-use requirement does not select that extra. Neither the
0.x browser-use release nor the newest 1.0.8 release selects the new harness.

The following minimal requirement pairs were passed to the ordinary resolver
with Python 3.14. Each returned exit 1; the receipt preserves the actual error
text. No dependency metadata was changed for these probes.

| Attempt | Resolver result |
| --- | --- |
| browser-use 0.13.14 + FastMCP 4.2.6 | browser-use requires MCP 2.1.1; FastMCP's client/server dependencies require MCP >=2.3.0 |
| browser-use 0.13.14 + browser-harness 0.1.15 | browser-use requires browser-harness 0.1.13 exactly |
| browser-use 1.0.8 + Pillow 13.0.0 | browser-use still requires Pillow 12.3.0 exactly |

FastMCP 4.1.2, the recorded patched 4.x floor, also requires MCP >=2.2.0.
Choosing that earlier patched release does not remove the MCP conflict.

The published browser-use 1.0.8 wheel was downloaded and checked against its
PyPI SHA-256, then inspected without installing it. Its `__init__.py` explicitly
lists `BrowserSession`, `ChatOllama`, and `ChatGroq` among removed public names;
its Agent implementation uses the new Browser/Pydantic AI contract. These
changes intersect this server's session lifecycle and provider mappings.
Consequently, adopting 1.x requires a migration with behavioral evidence and
still does not solve the Pillow constraint today.

Primary metadata:

- [browser-use 0.13.14](https://pypi.org/pypi/browser-use/0.13.14/json)
- [browser-use 1.0.8](https://pypi.org/pypi/browser-use/1.0.8/json)
- [browser-harness 0.1.13](https://pypi.org/pypi/browser-harness/0.1.13/json)
- [browser-harness 0.1.15](https://pypi.org/pypi/browser-harness/0.1.15/json)
- [FastMCP-slim 4.1.2](https://pypi.org/pypi/fastmcp-slim/4.1.2/json)
- [FastMCP-slim 4.2.6](https://pypi.org/pypi/fastmcp-slim/4.2.6/json)

## Executed repository checks

| Check | Observed result |
| --- | --- |
| Frozen development sync, CPython 3.14.7 | Passed |
| `uv lock --check` | Passed |
| `uv pip check` | 142 installed packages compatible |
| Full test suite, CPython 3.14.7 | 66 passed; 22 upstream deprecation warnings |
| Dependency-free immutable-input suite | 6 passed |
| Short external COPY-source preservation probe | Mutable `busybox:latest` rejected; declared build-stage alias skipped correctly |
| Ruff lint and format check | Passed |
| Server import | Passed |
| Frozen runtime vulnerability audit | Failed: 77 records in five packages |

Commands used uv 0.12.3. The full test suite and import command used
`uv run --frozen --with socksio==1.0.0` to support this worker's inherited SOCKS
proxy. That test-only overlay is absent from the committed runtime lock and
the audited export. The ordinary hosted commands remain unchanged.

Docker is unavailable in this worker. The hosted Python matrix, container,
and CodeQL results for the new documentation commit must be read separately
from the earlier run on `a0063336`; earlier passing jobs are not a new run.
No provider-driven browser journey was executed or qualified here.

## Preservation before closing superseded integration targets

PR #47 head `0e9545ab96dcca69a649bb81c14505a61159c2a7` is an ancestor of
PR #51's runtime head. Its full source history is retained, including the
public-API migration, input limits, isolated sessions, provider mapping,
Smithery schema, lock, and non-root container. The later Ollama correction is
already covered by the installed-adapter regression in #51.

PR #48 head `b5df4d6470405ae4904a9d20094983a0376a10cd` is not an ancestor, so
its complete six-file patch was compared by behavior:

| PR #48 contribution | Preserved in PR #51 |
| --- | --- |
| Immutable external Docker inputs | Current Python 3.14 and uv inputs have explicit manifest digests; obsolete Python 3.12/3.13 image selections are replaced |
| Full-SHA external Action references | Current CI uses full commit SHAs |
| Dependency-free hosted pin check | The `supply-chain` job in `.github/workflows/ci.yml` runs the standard-library suite on pull requests |
| Renovate Docker/Action refresh policy | Both rules remain, with lock maintenance and browser-use security review added |
| Enforcement tests | Original assertions remain; later code handles stage aliases, short external image names, reusable workflows, and named steps |
| Documentation of the gate boundary | README, SECURITY, and decision 0001 retain the distinction between immutable inputs and an audited runtime |

The reusable-workflow and short external-image review findings from #48 are
addressed in #51. Closing #47/#48 as superseded preserves their branches,
commits, and review history; it does not merge their code or close #8/#45/#49
as fixed. #51 is the sole integration vehicle.

## Remaining implementation decision

A supported release that relaxes browser-use's affected exact pins would
allow a normal lock refresh. Until that exists, the bounded repair cannot be
completed within published requirements. The alternative is explicit
ownership of a compatibility change to browser-use, including its harness
dependency edge, with ongoing security maintenance and tests of the actual
artifacts. The newly published harness may reduce the necessary fork scope;
its compatibility with browser-use 0.x has not been established by metadata.

That decision must preserve the existing reversal criteria: complete
dependency compatibility and unsuppressed audit, the Python matrix, actual
MCP lifecycle/cancellation checks, browser/screenshot/document behavior, and
container validation on the same candidate. A metadata-only graph or a green
unit suite cannot substitute for those checks. No speculative fork is adopted
by this follow-up.
