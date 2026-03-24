# ADR-015: Hook Test Helpers Must Clear Session-Injected Env Vars

Date: 2026-03-24
Status: Accepted

## Context

Claude Code's `session-resume.py` hook injects env vars (`ZIE_AUTO_TEST_DEBOUNCE_MS`,
`ZIE_MEMORY_ENABLED`, `ZIE_TEST_RUNNER`, etc.) into the running process to provide
fast-paths for other hooks. When pytest runs inside a Claude Code session, these
vars are present in `os.environ`. Any `run_hook()` helper that copies `os.environ`
via `{**os.environ}` silently inherits them, causing the subprocess to behave as
it would in a live session rather than in an isolated test environment.

## Decision

Every `run_hook()` test helper must explicitly clear all session-injected env
vars in its base environment before applying test-specific overrides:

```python
env = {**os.environ,
       "ZIE_MEMORY_API_KEY": "",
       "ZIE_MEMORY_ENABLED": "",
       "ZIE_AUTO_TEST_DEBOUNCE_MS": "",
       "ZIE_TEST_RUNNER": ""}
```

Tests that intentionally test env-var-driven fast-paths pass those vars via
`env_overrides`, which is applied after the base clear.

## Consequences

**Positive:** Hook tests always read from config files, not from the ambient session
state — deterministic results whether run inside or outside a Claude Code session.
**Negative:** New `run_hook()` helpers require this boilerplate; easy to forget.
**Neutral:** Tests that previously relied on inherited env vars must now pass them
explicitly via `env_overrides`.
