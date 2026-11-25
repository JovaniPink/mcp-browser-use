# MCP Browser Use documentation

The root [`README.md`](../README.md) is the current installation, runtime,
testing, and security entry point.

## Current references

- [`CONFIGURATION.md`](CONFIGURATION.md) — environment variables, defaults,
  parsing behavior, provider credentials, and browser runtime configuration.
- [`SECURITY.md`](SECURITY.md) — implemented safeguards, operator
  responsibilities, concurrency limits, and release checklist.

## Decision records

- [`decisions/0001-hold-unsafe-runtime-resolution.md`](decisions/0001-hold-unsafe-runtime-resolution.md)
  — the historical unsafe-resolution hold and its reversal criteria.
- [`decisions/0002-owned-repository-compatibility-build.md`](decisions/0002-owned-repository-compatibility-build.md)
  — the accepted owned packaging path for frozen checkout/Docker delivery,
  effective only after PR #51 passes its mandatory checks and is merged.

Decision records preserve why a consequential choice was made and the evidence
required to reverse it. Superseded records remain in the log with links to their
replacement.

## Evidence rules

The [owned-build receipt](validation/owned-runtime-compatibility-2026-11-25.md)
records the current compatibility candidate's exact inputs, local results,
and pending hosted browser/container gates. The
[earlier November 25 follow-up](validation/runtime-follow-up-2026-11-25.md)
preserves the upstream-only audit, published-dependency feasibility checks,
and integration-history evidence. The
[November 17 repair record](validation/runtime-repair-2026-11-17.md) preserves
the preceding code repairs and supported-runtime validation.

- Distinguish unit tests, dependency resolution, vulnerability audit, container
  build, MCP-client integration, and isolated-browser operation.
- Never publish provider keys, authenticated CDP endpoints, profile contents,
  task payloads, screenshots, or downloads containing private data.
- Date upstream research and link the exact release metadata, advisories, lock,
  commit, and test environment used.
