---
slug: audit-pytest-markers-consolidate
status: approved
date: 2026-04-01
---
# Spec: Consolidate pytest marker declarations into pytest.ini

## Problem

The `error_path` pytest marker is registered via `pytest_configure` in
`tests/conftest.py` using `config.addinivalue_line(...)`. Meanwhile, `pytest.ini`
only declares the `integration` marker. This creates a split: one marker is
declared in config, another via Python code at runtime.

The consequence is that running `pytest --strict-markers` would raise a
`PytestUnknownMarkWarning` for `error_path` — not because it is undeclared,
but because it is declared through a non-standard path that `--strict-markers`
does not treat equivalently across all pytest versions. Per pytest docs, all
custom markers should be declared under the `[pytest] markers =` section in
`pytest.ini` (or `pyproject.toml`).

Additionally, there is no `--strict-markers` in `addopts`, so any future
undeclared marker added by accident will silently pass rather than fail loudly.

Affected files:
- `pytest.ini` — missing `error_path` marker declaration
- `tests/conftest.py` — `pytest_configure` hook used purely to register a marker
- 6 test files use `@pytest.mark.error_path` and must continue to pass

## Proposed Solution

1. Add the `error_path` marker declaration to the `markers =` block in
   `pytest.ini`, mirroring the existing `integration` entry.
2. Remove the `pytest_configure` function from `tests/conftest.py` entirely,
   as it will no longer serve any purpose.
3. Add `--strict-markers` to `addopts` in `pytest.ini` so any undeclared marker
   added in the future causes an immediate, visible failure.
4. Run the full unit test suite to confirm all 6 files using
   `@pytest.mark.error_path` still pass with no warnings.

No other files need to change. The marker string description is preserved
verbatim when moved to `pytest.ini`.

## Acceptance Criteria

- [ ] AC1: `pytest.ini` declares both `integration` and `error_path` markers under `markers =`
- [ ] AC2: `tests/conftest.py` no longer contains a `pytest_configure` function
- [ ] AC3: `pytest.ini` `addopts` includes `--strict-markers`
- [ ] AC4: `make test-fast` (or `pytest -m error_path`) exits 0 with no marker warnings
- [ ] AC5: `make test-ci` exits 0 — no regressions in any test file

## Out of Scope

- Changing the marker name or description
- Migrating from `pytest.ini` to `pyproject.toml`
- Adding new markers or new tests
- Any changes to hook source files in `hooks/`
