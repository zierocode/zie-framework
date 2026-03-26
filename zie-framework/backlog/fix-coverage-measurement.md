# Fix Coverage Measurement Infrastructure

**Source**: audit-2026-03-24b C2 (Critical — Agent C)
**Effort**: M
**Score impact**: +15 (Critical eliminated → Quality +15)

## Problem

All 80+ unit tests invoke hooks via `subprocess.run()`. This is correct for
integration-style testing but prevents pytest-cov from measuring line execution.
14 of 22 hooks report 0% coverage despite having dedicated test files with passing
tests. The reported 20% total is meaningless — we can't identify truly untested
paths or set coverage gates.

## Motivation

Without accurate coverage measurement:
- Cannot set `--cov-fail-under` threshold in CI
- Cannot identify genuinely untested code paths vs subprocess-tested ones
- Cannot improve coverage systematically

## Scope

Two valid approaches — choose one:

**Option A (Recommended): Subprocess coverage via `coverage.py` subprocess tracking**
- Add `COVERAGE_PROCESS_START=.coveragerc` env var to subprocess test invocations
- Configure `.coveragerc` with `source = hooks` and `parallel = True`
- Add `coverage combine` step after tests

**Option B: Migrate to import-based tests for core logic**
- Refactor hooks to expose testable functions (already partially done: `evaluate()`
  in safety-check.py)
- Test via `from hooks.safety_check import evaluate` pattern
- Keep subprocess tests as integration layer only

**Both approaches:**
- Target: 70%+ measured coverage for `hooks/`
- Add `--cov-fail-under=70` to Makefile `test-unit`

## Acceptance Criteria

- [ ] Coverage report accurately reflects executed code paths
- [ ] At least 70% measured coverage for hooks/
- [ ] Coverage gate prevents regression in CI
- [ ] `make test-unit` fails if coverage drops below threshold
