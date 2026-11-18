# Runtime repair and validation — November 17, 2026

## Result

The two repository-owned defects are fixed, and the targeted compatible
dependency refresh removes 64 advisory records and 12 affected packages from
the previous lock. The runtime audit still fails on 76 records in five packages.
The release remains held under [decision 0001](../decisions/0001-hold-unsafe-runtime-resolution.md).

This work starts from PR #51 commit
`29d455d752014ce11899a6aadefa7d19e6d69c56`. Dates in this record use
America/New_York; execution occurred on November 18 UTC.

## Behavior repaired

- **Ollama configuration:** explicit temperatures, including `0.0`, are passed
  through the installed adapter's supported `ollama_options`. An unset value
  remains `None`, retaining the provider default. The regression uses the real
  adapter's `ainvoke()` with a recording network client: the explicit-value
  cases failed before the fix and pass afterward. No provider call is made.
- **Immutable workflow inputs:** job-level reusable workflows and named-step
  `uses:` declarations are now inspected. A fixture with both a valid pinned
  checkout and a mutable reusable workflow was incorrectly accepted before
  the fix. It is rejected afterward. Pinned external references and local
  references remain accepted. Docker stage-alias handling is unchanged.

The workflow scanner is a dependency-free checker for the repository's
block-style declarations, not a general YAML parser.

## Compatible dependency repair

`browser-use` moves from 0.13.10 to 0.13.14, retaining the existing public
Agent, BrowserSession, provider, proxy, timeout, and concurrency contracts.
Affected packages are refreshed within published requirements; unrelated
locked versions, including OpenAI 2.26.0 and Anthropic 0.76.0, are retained.
Multidict stays on the patched 6.x line rather than taking an unnecessary major
upgrade. The [machine-readable audit receipt](runtime-audit-2026-11-17.json)
contains all 16 changed package families and the remaining advisory IDs.

The Python requirement is now `>=3.11.5`. SoupSieve 4.1.1 requires that minimum;
the previous `>=3.11` requirement retained vulnerable SoupSieve 2.10 for
Python 3.11.0–3.11.4. The new universal lock has no such fallback. An actual
`uv sync --frozen --python 3.11.4 --no-python-downloads` invocation was rejected
because that interpreter does not satisfy the project requirement.

## Executed checks

Resolution, synchronization, and exports used **uv 0.12.3**. Local Python test
commands used `uv run --frozen --with socksio==1.0.0 pytest -q`: this workspace
inherits a SOCKS proxy, and the extra supplies its transport without disabling
proxy controls or changing the committed runtime lock. The canonical hosted
matrix still runs the repository's unmodified frozen commands.

| Check | Observed result |
| --- | --- |
| Dependency-free immutable-input suite | 6 passed; both new regressions failed before the fix |
| Full suite, CPython 3.11.15 | 66 passed |
| Full suite, CPython 3.12.14 | 66 passed |
| Full suite, CPython 3.13.5 | 66 passed |
| Full suite, CPython 3.14.7 | 66 passed; 22 upstream deprecation warnings |
| `uv lock --check` | Passed |
| Frozen development sync | Passed on all four local interpreters |
| `uv pip check` | Passed; 142 packages compatible in the primary 3.12 environment |
| Server import and all seven real provider-adapter constructions | Passed without provider requests |
| `uv build` | Source distribution and wheel built |
| Ruff lint, format check, and `git diff --check` | Passed |
| Unsuppressed runtime audit, CPython 3.12.14, pip-audit 2.10.1 | Failed: 76 advisory records across five packages |

Hosted checks must be read back after pushing; PR #51 records their observed
status separately from these local results.
Docker is unavailable in this local worker; the existing hosted container job
owns the image build, Chromium version, import, and non-root-user checks.
Neither unit tests nor those image smoke checks establish a live model-driven
browser journey or qualify production release.

## Exact audit inputs and remaining constraints

- `pyproject.toml` SHA-256:
  `4ef1aef9c768b3c469f3eb2a5579e2a203ec53eebfae790fe4784816303a8209`
- `uv.lock` SHA-256:
  `ac34569170bb0ca80c46dcd89dea213c161fa53fcd04878f20f86b97a73ca042`

The previous exact lock reported 140 records across 17 packages. The current
export was audited with `pip-audit==2.10.1`, without ignores or overrides:

| Package | Locked | Advisory records | Recorded fixed floor on the selected major line |
| --- | --- | ---: | --- |
| AnyIO | 4.12.1 | 2 | 4.14.2 |
| FastMCP | 4.0.3 | 2 | 4.1.2 |
| MCP | 2.1.1 | 4 | 2.2.0 |
| Pillow | 12.3.0 | 42 | 13.0.0 |
| pypdf | 6.16.2 | 26 | 6.21.4 |

These are the tool's advisory records, not 76 independent application defects
or proof of exploitability. Fixed floors are source-dated evidence, not a
completed compatible resolution or a guarantee against future advisories.

A normal resolver rejects browser-use 0.13.14 with patched FastMCP 4.1.2:
browser-use requires `mcp==2.1.1`, whereas FastMCP requires `mcp>=2.2.0`.
The other vulnerable versions are also constrained by upstream exact pins.

Browser-use 1.0.6 is not adopted: it changes the engine to model-written Python,
removes or changes current configuration/provider APIs, and still requires the
affected Pillow version. A separate metadata-only compatibility-fork probe
changing the four browser-use pins also fails: browser-harness 0.1.13
independently requires `pillow==12.3.0`, conflicting with Pillow 13.0.0.
Browser-harness 0.1.13 remains the latest published release at this check.

Consequently, removing the remaining hold requires compatible published
upstream metadata or an explicitly authorized, maintained compatibility change
covering both browser-use and browser-harness. No such fork was adopted by this
repair, and this record does not change the existing approval requirements.

Primary metadata checked:

- [Browser-use 0.13.14](https://pypi.org/pypi/browser-use/0.13.14/json)
- [FastMCP-slim 4.1.2](https://pypi.org/pypi/fastmcp-slim/4.1.2/json)
- [Browser-use 1.0.6](https://pypi.org/pypi/browser-use/1.0.6/json)
- [Browser-harness 0.1.13](https://pypi.org/pypi/browser-harness/0.1.13/json)
- [SoupSieve 4.1.1](https://pypi.org/pypi/soupsieve/4.1.1/json)
