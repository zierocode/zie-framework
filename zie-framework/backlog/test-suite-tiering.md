# Test Suite Tiering — Fast Dev Loop vs Full CI

## Problem

The test suite has 1,601 tests today, growing ~+50-100 per sprint. All tests run
together in `make test-unit`. As the suite grows, local dev feedback loops slow
down — a developer changing one hook file should not wait for 1,600 unrelated tests.

## Motivation

Fast local feedback is the core of TDD. If `make test-unit` takes 30+ seconds,
developers skip it. Tiering separates "run always" (changed-file-related) from
"run before commit" (full suite) without removing any tests or losing coverage.

## Rough Scope

- Add `make test-fast` target: uses `pytest --lf` (last-failed) + `pytest -x` on
  files changed since last commit (via `git diff --name-only` → map to test files)
- Add `make test-ci` alias for current `make test-unit` (full suite, for CI/pre-commit)
- Document in CLAUDE.md: use `make test-fast` during TDD RED/GREEN, `make test-ci`
  before commit
- Update `/zie-implement` tdd-loop skill to reference `make test-fast` for RED/GREEN
  phase and `make test-ci` for REFACTOR verification
- Tests: test-fast target exists and runs a subset, test-ci runs full suite
