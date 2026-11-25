# Owned runtime compatibility receipt - November 25, 2026

## Result and boundary

The owned candidate passes the local checks recorded below. Its fresh,
unsuppressed runtime audit reports **128 distributions, zero reported
vulnerabilities, and zero skipped entries**, including `browser-use` 0.13.14.
This is a different graph from the earlier
[77-record upstream-only audit](runtime-follow-up-2026-11-25.md).

**Hosted qualification of the final published head is pending.** Local
component and checkpointed subprocess results do not establish real-browser
or container compatibility. [Decision 0002](../decisions/0002-owned-repository-compatibility-build.md)
accepts the bounded frozen-checkout/Docker path, effective only when PR #51 is
merged after its mandatory checks pass. This receipt does not record a package
release, deployment, paid provider journey, or completed adoption.

## Exact inputs

These SHA-256 values identify the local candidate and captured evidence before
publication. The final PR's checks must validate the same reviewed inputs; a
previous commit's hosted results cannot qualify a changed candidate.

| Input | SHA-256 |
| --- | --- |
| `pyproject.toml` | `7bd9ebdaa036f064ab8085a36a674f1dd0c63540743f41a3715727213211814f` |
| `uv.lock` | `8e24669b477fe34ce03403f4d68bb0728f93e3e91197d20f0b9fcae638232cc9` |
| `src/mcp_browser_use/server.py` | `ce30bd2e289526f9b61e329da547b71f04d7f97b1bb000f179cbdeb696e26294` |
| `tests/test_server_cancellation.py` | `a71566142ba6ae384e3f2a0a4ee15426074201e9d8bc77f27de2a9e17907e6c5` |
| Owned browser-use wheel, build `1mcbu1` | `f2cce85e872041b6407d65ae14b635df10f1f443cda2c2e814169ea330e9bfd1` |
| `compat/browser-use/provenance.json` | `2cb497cf1f70cdd04c00eca4f65882824ef744f72b9b9440081bf31ba4724554` |
| Verified upstream 0.13.14 source archive | `9bb2f3d7ea215bf67b415c8e6e546413a3712ac5ea775b223b452189f4582d9d` |
| `compat/browser-use/source.patch` | `b2db76d2b49d46b56c727c3cbffa30ec4a7c45c040740b253f96b78ca3e12ca3` |
| Final frozen runtime requirements export | `c34bf0f3a7e883549a230a4053adb7b7392148539ddac7521b2927caef99f418` |
| Captured runtime audit JSON | `c401fbfc8458255320c9749efa095a7bd2a3d6fb7192e3706d23bbbb0439e9b2` |

The [provenance record](../../compat/browser-use/provenance.json) also binds
the MIT license, upstream manifest, build tools, and all 182 runtime files.
Those runtime bytes match the verified upstream archive. The packaging patch
changes declared requirements and the summary while retaining distribution
name/version for advisory matching. The resolver consumes the actual rebuilt
wheel; no dependency override, forced no-dependency install, or advisory
allowlist was used.

Selected versions are AnyIO 4.14.2, FastMCP 4.2.6, MCP 2.3.0,
browser-harness 0.1.15, Pillow 13.0.0, and pypdf 6.21.4. The harness's optional
`mcp` extra is not selected or qualified by this graph.

## Executed local checks

The environment was Linux with CPython 3.14.7 and uv 0.12.3. The audit covers
the 128 runtime distributions selected for that environment; it does not
qualify every platform marker or unselected optional extra. Reproduction additionally
used Hatchling 1.32.0, wheel 0.48.0, and the recorded `SOURCE_DATE_EPOCH`.

The local pytest and checkpoint transport commands used an isolated
`--with socksio==1.0.0` overlay for this workspace's proxy support:

```sh
uv tool run --from uv==0.12.3 uv run --frozen --with socksio==1.0.0 pytest -q
uv tool run --from uv==0.12.3 uv run --frozen --with socksio==1.0.0 python compat/browser-use/check_mcp_transport.py --checkpoint-only
```

That test-only overlay is absent from the committed lock, frozen runtime
export, and audit. Hosted checks use the committed environment without it.

| Check | Observed result and scope |
| --- | --- |
| Frozen environment, `uv lock --check`, `uv pip check` | Passed; 134 installed distributions compatible |
| Full test suite | 70 passed, with 22 upstream deprecation warnings |
| Cleanup regressions and existing server tests | 23 passed, including four new cancellation/shutdown cases |
| Dependency-free immutable-input tests | Six passed |
| Ruff lint and format checks | Passed |
| `compat/browser-use/verify.py` | Passed artifact, metadata, source-hash, and license checks |
| `compat/browser-use/build.py --check` | Reproduced the exact owned-wheel hash above |
| Runtime-only `pip-audit` 2.10.1 | Exit 0; 128 distributions, zero findings, zero skipped; owned browser-use included |
| `check_mcp_transport.py --checkpoint-only` | Actual stdio subprocess startup, initialization, tool discovery, cancellation/reuse, disconnect, and server exit passed in auto and legacy modes; deterministic lifecycle fixtures, zero real browser PIDs exercised |
| Ordinary application-wheel installation probe | Expected `ResolutionImpossible`; the application requires AnyIO 4.14.2 while published browser-use requires 4.12.1 |

The last row establishes the delivery boundary. An application wheel does not
carry `tool.uv.sources`; published browser-use's MCP 2.1.1 requirement also
conflicts with the selected FastMCP graph. The observed first resolver error
was the AnyIO conflict, not the MCP conflict.

### Cancellation defects reproduced and repaired

The first failing regression showed that an AnyIO-cancelled request did not
finish its awaited browser cleanup before the next request could reuse the
run slot. The second showed native `Task.cancel()` during graceful stop could
be consumed instead of preserved. Neither defect is attributed to the
dependency upgrade merely because the compatibility work exposed it.

The repaired path shields cleanup, retains the run slot through bounded
attempts, uses a 10-second graceful-stop deadline and 5-second forced-stop
fallback, and re-raises the original native cancellation. Tests also cover
the graceful deadline and failure of the forced attempt. Failures are logged;
these bounds do not guarantee browser termination if both attempts fail or
the server is forcibly killed externally.

### Document and image components; local browser limit

At UID 1000, a real ReportLab 4.4.9 three-page PDF passed through
`FileSystem.read_file_structured(external_file=True)` and pypdf 6.21.4. All
three text/page markers survived. The file was 2,371 bytes, SHA-256
`55cace6942ef6e351b4e68fc95a8044aa21f06585c2563aea7c1b63211207553`.
AnyIO-backed ScreenshotService storage round-tripped a synthetic PNG
byte-identically; Pillow 13 resized it to 400 x 225, and the harness helper's
`max_dim=640` path produced 640 x 360 using a fake CDP response. No Python
non-loopback connection was attempted.

Those component checks used standalone probe SHA-256
`6255e53c3fd8c397a95d5320032f2f55db5f1a05f003d18dad1ba218a9100f46`.
The integrated probe differs only in import grouping, but its required full
runtime execution is still pending. Component success does not prove live
CDP capture, harness daemon/IPC behavior, an LLM Agent loop, or UID 10001
operation; the PDF fixture does not qualify encrypted, malformed, or OCR PDFs.

The full host probe failed rather than skipped: `/usr/bin/chromium --version`
exited 127 because its `/usr/lib/chromium` symlink targets the absent
`/opt/codex/browsers/chromium`. Docker was unavailable locally. No browser
download or provider call was used to substitute for the missing runtime.

## Mandatory hosted qualification

On the final published PR head, require the existing Python 3.11-3.14 matrix,
dependency consistency, immutable-input tests, owned-source reproduction,
unsuppressed runtime audit, server import, test/runtime Docker builds, and
configured security checks. The runtime image must run both
[browser/document](../../compat/browser-use/browser_document_smoke.py) and
[MCP transport](../../compat/browser-use/check_mcp_transport.py) probes as
UID 10001 with `--network none`, offline mode, and telemetry disabled.

The browser probe must use the application's session factory, local fixture
navigation, actual screenshots, AnyIO storage, Pillow resizing, a live-CDP
harness screenshot bridge, and PDF extraction. The MCP probe must verify
actual browser/server process exit on cancellation and disconnect, plus a
subsequent request. Missing Chromium is a failing gate. The screenshot bridge
does not qualify harness IPC, and the disposable fixture's explicit
no-sandbox setting does not qualify Chromium's OS sandbox. Merge and decision
effectiveness remain contingent on these results and final integration review.
