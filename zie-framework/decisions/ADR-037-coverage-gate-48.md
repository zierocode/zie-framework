# ADR-037: Raise Coverage Gate from 43% to 48%

**Date:** 2026-04-01
**Status:** Accepted
**Deciders:** Zie

## Context

ADR-027 set the coverage gate at 43% — the actual coverage level at the time
(v1.7.0). That ADR explicitly noted the gate should be raised incrementally as
coverage grows. Without `sitecustomize.py` installed in the venv, subprocess-
spawned hooks (auto-test.py, wip-checkpoint.py, etc.) report 0% coverage, so
the measurable coverage is limited to directly-imported modules.

## Decision

Raise `--fail-under` from `43` to `48` in the `Makefile` `test-unit` and
`test-ci` targets. This reflects the current directly-importable coverage
level. Target is 70% once sitecustomize.py subprocess tracking is available.

## Consequences

- CI fails if coverage drops below 48% (previously 43%).
- Closes a 5-point gap that allowed silent regressions.
- Future gate raises should follow the same pattern: measure first, raise
  second, document in a new ADR.

## Related

- ADR-027: Original coverage gate (43%)
- ADR-026: Coverage report format
- Makefile `test-unit` / `test-ci` targets
