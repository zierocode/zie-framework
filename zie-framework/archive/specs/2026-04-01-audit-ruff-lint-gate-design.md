---
slug: audit-ruff-lint-gate
status: draft
date: 2026-04-01
---
# Spec: Add ruff lint + format gate to pre-commit, Makefile, and CI

## Problem

No Python linter or formatter runs at any stage of the development cycle.
`bandit` (SAST) and `markdownlint` are configured, but neither catches Python
logic errors: unused imports, undefined names, shadowed variables, or style
drift. A developer can commit code that `pyflakes` would flag immediately, with
no automatic signal until a human review.

`hooks/utils.py` already uses type annotations (`CONFIG_SCHEMA: dict`,
`-> str`, `-> dict`), confirming the codebase expects readable, well-typed
Python. The tooling does not yet enforce this expectation.

## Proposed Solution

Install `ruff` as the project's Python linter and formatter across three
enforcement layers:

### 1. `.pre-commit-config.yaml` — commit-time gate

Add two hooks from `astral-sh/ruff-pre-commit`:
- `ruff` — lint with `--select E,F,W`
- `ruff-format` — format check with `--check` (no auto-fix)

Runs on every `git commit`. Fail fast before bad code reaches the remote.

### 2. `Makefile` — new `lint` target

Add a `lint` target that runs:
```
ruff check --select E,F,W hooks/ tests/ scripts/
ruff format --check hooks/ tests/ scripts/
```

Wire `lint` into the existing `test` and `test-ci` targets so it is part of
every full test run.

### 3. `ci.yml` — lint step before tests

Add `ruff` to the `pip install` line and add a `Run lint` step that executes
`make lint`. The lint step runs before the test step so CI fails fast on
trivial errors.

### 4. `pyproject.toml` — ruff configuration

Create `pyproject.toml` (or `ruff.toml`) with a `[tool.ruff]` section:
```toml
[tool.ruff]
select = ["E", "F", "W"]
line-length = 88
exclude = [".git", "__pycache__", "node_modules"]
```

No ignores by default. If bare `except:` clauses in hooks trigger E722, add
`"E722"` to the `ignore` list only after checking the actual count — the
hook error-handling convention uses `except Exception` (explicit), not bare
`except`, so E722 violations may be zero.

## Acceptance Criteria

- [ ] AC1: `.pre-commit-config.yaml` includes `astral-sh/ruff-pre-commit` with
  both `ruff` (lint) and `ruff-format` (format check) hooks configured
- [ ] AC2: `make lint` runs `ruff check --select E,F,W` and
  `ruff format --check` against `hooks/`, `tests/`, and `scripts/`; exits
  non-zero on any violation
- [ ] AC3: `make test-ci` and `make test` invoke `make lint` (lint runs as part
  of full test suite)
- [ ] AC4: `ci.yml` installs `ruff` and has a dedicated "Run lint" step that
  runs `make lint` before the "Run tests" step
- [ ] AC5: A `pyproject.toml` (or `ruff.toml`) exists at repo root with
  `[tool.ruff]` selecting `E`, `F`, `W` rules and `line-length = 88`
- [ ] AC6: `ruff check` passes on the current codebase with zero violations
  (fix any pre-existing issues as part of implementation)
- [ ] AC7: `ruff format --check` passes on the current codebase with zero
  violations (format any files that differ as part of implementation)
- [ ] AC8: Auto-fix mode (`--fix`, `--unsafe-fixes`) is NOT enabled in any
  configuration — check only, no silent mutations

## Out of Scope

- `mypy` / `pyright` type checking
- `ruff` auto-fix mode (`--fix`) wired into pre-commit or CI
- Changing existing code style beyond what is required to pass lint/format
  checks
- Additional rule sets beyond `E`, `F`, `W` (e.g. `I` isort, `N` naming,
  `ANN` annotations)
- Editor / IDE integration (`.vscode/settings.json` etc.)
- `ruff` configuration in `hooks/` itself (hooks are not a ruff plugin)
