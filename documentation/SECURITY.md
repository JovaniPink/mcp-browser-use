# Security Model

This server gives an LLM control of a real browser. Treat every task, page, download, screenshot,
and browser profile as untrusted input. This document describes implemented safeguards and the
operator responsibilities that remain outside the repository.

## Implemented Boundaries

- `run_browser_agent` trims and validates tool input before allocating a model or browser session.
- Tasks and optional context are each limited to 20,000 characters.
- `MCP_MAX_STEPS` is limited to 1–100 and `MCP_MAX_ACTIONS_PER_STEP` to 1–20; invalid values use
  documented defaults.
- Every tool call creates a browser session and attempts graceful cleanup, then forced cleanup when
  supported.
- Browser web security stays enabled unless `BROWSER_USE_DISABLE_SECURITY=true` is explicitly set.
- Proxy configuration is omitted from debug logs.
- CDP endpoints are redacted from debug logs because URLs may contain usernames, passwords, or
  access tokens.
- `BROWSER_USE_ALLOWED_DOMAINS` can restrict navigation to an operator-defined allowlist.

These controls reduce accidental resource consumption and credential disclosure. They do not make
untrusted browser automation safe by themselves.

## Operator Responsibilities

1. Run untrusted tasks in an isolated container or virtual machine.
2. Use ephemeral browser profiles unless a task explicitly requires persistence. A persisted
   profile may contain cookies, account sessions, browsing history, and saved form data.
3. Keep provider credentials in an MCP client secret store or dedicated secret manager. Never put
   real credentials in `sample.env.env`, source control, screenshots, issue comments, or logs.
4. Bind Chrome DevTools Protocol endpoints to localhost or place them behind an authenticated
   tunnel. An exposed CDP endpoint grants browser control.
5. Keep browser security enabled. If a test requires disabled web security, isolate that browser
   from authenticated sessions and other workloads.
6. Restrict allowed domains for bounded workflows and review any expansion deliberately.
7. Treat clipboard access and downloads as host-side effects. Use a dedicated runtime when a task
   may encounter hostile content.
8. Rotate any credential that appears in a task, URL, browser profile, log, or artifact.

## Concurrency Boundary

The current `AgentState` is a process-wide singleton. Operate this server as a single active agent
per process. Multi-tenant or concurrent execution requires replacing that singleton with
request-scoped state and proving session isolation first.

## Dependency Boundary

The Python 3.14/browser-use upgrade is intentionally held by
[#45](https://github.com/JovaniPink/mcp-browser-use/issues/45). Upstream currently hard-pins
transitive packages with published advisories. Do not suppress those advisories or force versions
that fail the package metadata contract. Unit tests, imports, and a successful container build are
not substitutes for a clean resolved dependency audit.

## Release Checklist

- run the complete test suite on every supported Python version
- verify the installed environment has no dependency conflicts
- audit the exact resolved production dependency set
- build and smoke-test the runtime container when Docker files or dependencies change
- confirm task/context limits and CDP redaction tests remain present
- keep the README and configuration reference aligned with actual defaults and limits

## Reporting

Open a private security report through GitHub when disclosure would expose credentials or a usable
exploit. For non-sensitive hardening requests, open a normal issue with the affected boundary,
reproduction steps, and the exact version or commit tested.
