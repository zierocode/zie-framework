# Add ruff linter to pre-commit, Makefile, and CI

**Severity**: Medium | **Source**: audit-2026-04-01

## Problem

No Python linter or formatter is configured in pre-commit, Makefile, or CI.
`bandit` (SAST) and `markdownlint` run, but neither catches Python logic
errors — unused imports, shadowed variables, wrong argument types, unreachable
code.

`hooks/utils.py` already uses type annotations (`-> str`, `-> dict`, etc.),
so `ruff check` and `mypy`/`pyright` would produce immediate signal. The
pre-commit hook currently has no Python linting step.

`ruff` is the current Python community standard (10-100x faster than flake8,
covers formatting + linting in one tool per the Python Developer Tooling
Handbook 2025).

## Motivation

Add `ruff` to:
- `.pre-commit-config.yaml` (lint + format check on commit)
- `Makefile` (`make lint` target, included in `make test-ci`)
- `ci.yml` (gate step before test run)

Start with `ruff check --select E,F,W` to catch the highest-signal errors
without being overly strict.
