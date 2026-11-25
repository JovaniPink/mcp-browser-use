# Owned browser-use compatibility build

This directory contains the repository-owned packaging build used by this
checkout's frozen `uv` installation and Docker build. It is an explicit derivative
of the verified upstream `browser-use` 0.13.14 source distribution. The 182
`browser_use/` runtime files are byte-for-byte identical to that source. The MIT
license is preserved in `LICENSE` and inside the wheel.

The source patch changes the package summary and declared dependency pins:

| Dependency | Upstream pin | Owned build pin |
| --- | --- | --- |
| AnyIO | 4.12.1 | 4.14.2 |
| MCP | 2.1.1 | 2.3.0 |
| Pillow | 12.3.0 | 13.0.0 |
| pypdf | 6.16.2 | 6.21.4 |
| browser-harness | 0.1.13 | 0.1.15 |

The application separately pins FastMCP 4.2.6 and directly declares AnyIO 4.14.2
for its cancellation-safe cleanup. These are ordinary declared dependencies;
the lock is resolved from the actual built wheel. No dependency override,
`--no-deps` installation, or advisory exclusion is used.

## Provenance and reproduction

`provenance.json` records the upstream source URL and SHA-256, reviewed source
patch and manifest hashes, build tools, original license, and every runtime file
hash. `source.patch` applies to the verified upstream source manifest. The
artifact is:

```text
browser_use-0.13.14-1mcbu1-py3-none-any.whl
SHA256: f2cce85e872041b6407d65ae14b635df10f1f443cda2c2e814169ea330e9bfd1
```

The standard wheel build tag `1mcbu1`, explicit package summary, and provenance
identify this owned build. Distribution name `browser-use` and version `0.13.14`
are retained so vulnerability tools continue to assess the upstream runtime
identity. The full runtime audit includes this distribution.

From the repository root:

```sh
python compat/browser-use/verify.py
python compat/browser-use/build.py --check
```

Verification uses the standard library and checks the committed artifact and
inputs without network access. Reproduction downloads the hash-pinned upstream
source, checks and applies the patch, verifies that all runtime source bytes are
unchanged, and builds with Python 3.14.7, uv 0.12.3, the upstream-pinned Hatchling
1.32.0, wheel 0.48.0, and the recorded `SOURCE_DATE_EPOCH`. It fails if the rebuilt
artifact differs from the committed SHA-256. `--output PATH` can retain that
verified wheel. The CI reproduction job runs the same check.

## Installation scope

`[tool.uv.sources]` selects this local wheel, and `uv.lock` binds its SHA-256.
Docker copies and verifies this directory before its frozen dependency layer.
Use the repository's frozen checkout commands or its Docker build.

An independently built application wheel does not carry the `uv.sources`
mapping. An ordinary `pip install --dry-run` of that application wheel currently
fails dependency resolution: the application requires AnyIO 4.14.2 while the
published upstream browser-use 0.13.14 requires AnyIO 4.12.1. The published
upstream MCP 2.1.1 pin also conflicts with FastMCP 4.2.6's MCP 2.3 requirement.
Standalone package installation and registry publication are therefore outside
this integration's supported scope. Do not work around those conflicts with
forced installations.

## Compatibility checks

The server exposes its existing `run_browser_agent` tool. Qualification covers
that application surface and the exercised document/image operations. It does
not establish support for browser-harness daemon/IPC tools, optional extras, or
every upstream agent feature. In particular, the unselected harness `[mcp]`
extra still pins MCP 2.1.1.

```sh
# Actual stdio protocol, checkpointed lifecycle fixture; no browser claim.
uv run --frozen python compat/browser-use/check_mcp_transport.py --checkpoint-only

# Required real-browser modes, executed by CI inside the runtime container.
python compat/browser-use/browser_document_smoke.py --chromium /usr/bin/chromium
python compat/browser-use/check_mcp_transport.py --browser-executable /usr/bin/chromium
```

CI runs both real-browser commands as runtime UID 10001 with `--network none`,
`BROWSER_USE_OFFLINE=1`, and telemetry disabled. They use isolated local fixtures,
profiles, and subprocesses without provider credentials. A missing browser is a
failure. Browser checks exercise actual screenshots, AnyIO screenshot storage,
Pillow resizing, a real-CDP harness screenshot bridge, and multipage PDF
extraction. MCP checks exercise installed startup, request cancellation,
subsequent requests, disconnection, awaited cleanup, and owned browser/server
process exit with PID creation-time matching. They do not run a paid model
journey. Fixture container execution does not qualify Chromium's OS sandbox.

The scoped adoption decision and its required gates are recorded in
[decision 0002](../../documentation/decisions/0002-owned-repository-compatibility-build.md).
Any later patch or artifact update needs renewed provenance, dependency review,
and the same applicable checks. This directory creates no public package release
or open-ended compatibility maintenance promise.
