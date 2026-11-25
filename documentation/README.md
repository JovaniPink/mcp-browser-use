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
  — why the Python/browser-use modernization remains held instead of forcing or
  suppressing an unsafe dependency resolution.

Decision records preserve why a consequential choice was made and the evidence
required to reverse it. Superseded records remain in the log with links to their
replacement.

## Evidence rules

The [November 25 follow-up](validation/runtime-follow-up-2026-11-25.md)
contains the current audit, published-dependency feasibility checks, and
preservation evidence for the single integration candidate. The
[November 17 repair record](validation/runtime-repair-2026-11-17.md) preserves
the preceding code repairs and supported-runtime validation.

- Distinguish unit tests, dependency resolution, vulnerability audit, container
  build, MCP-client integration, and isolated-browser operation.
- Never publish provider keys, authenticated CDP endpoints, profile contents,
  task payloads, screenshots, or downloads containing private data.
- Date upstream research and link the exact release metadata, advisories, lock,
  commit, and test environment used.
