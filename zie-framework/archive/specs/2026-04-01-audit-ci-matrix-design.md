---
slug: audit-ci-matrix
status: draft
date: 2026-04-01
---
# Spec: Add CI Matrix — macOS + Python 3.11

## Problem

`ci.yml` runs a single job on `ubuntu-latest` using `python-version-file: .python-version`
(Python 3.13). No matrix strategy is defined.

Claude Code's primary user platform is macOS. Several hooks use subprocess behavior
(SIGTERM handling, `/tmp` path semantics) that differs between macOS and Linux.
`hooks/utils.py` uses `str | None` union syntax (Python 3.10+), but Python 3.11
remains common in user environments. A bug affecting Python 3.11 or macOS would
pass CI undetected.

## Proposed Solution

Replace the single-job configuration with a `strategy.matrix` that covers
`os: [ubuntu-latest, macos-latest]` × `python-version: [3.11, 3.13]` — producing
4 jobs per push/PR.

Replace `python-version-file: .python-version` with `python-version: ${{ matrix.python-version }}`
so each matrix leg sets its own version. All other steps (install, `make test-unit`)
remain identical across legs.

No new scripts, no conditional steps, no allowed failures — all 4 jobs must pass.

## Acceptance Criteria

- [ ] AC1: `ci.yml` defines `strategy.matrix` with `os: [ubuntu-latest, macos-latest]`
      and `python-version: [3.11, 3.13]`.
- [ ] AC2: `runs-on: ${{ matrix.os }}` replaces the hardcoded `ubuntu-latest`.
- [ ] AC3: `python-version: ${{ matrix.python-version }}` replaces
      `python-version-file: .python-version` in the `setup-python` step.
- [ ] AC4: Install and test steps (`pip install …`, `make test-unit`) are unchanged
      and shared across all matrix legs.
- [ ] AC5: No `continue-on-error` or `fail-fast: false` overrides — all 4 jobs must
      pass for the workflow to succeed.
- [ ] AC6: Existing trigger branches (`main`, `dev`) and event types (`push`,
      `pull_request`) are preserved unchanged.
- [ ] AC7: `make test-unit` passes locally on Python 3.11 (no 3.13-only syntax used
      in hook source files).

## Out of Scope

- Windows runners.
- Python versions below 3.11 or above 3.13.
- Integration tests in CI (require live Claude session).
- Coverage upload / artifact publishing.
- Dependabot updates to `actions/setup-python`.
