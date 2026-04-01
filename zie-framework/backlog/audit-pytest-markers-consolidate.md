# Move error_path marker declaration from conftest.py to pytest.ini

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

The `error_path` pytest marker is registered via `pytest_configure` in
`conftest.py` but `pytest.ini` only declares the `integration` marker.
Running `pytest --strict-markers` would raise `PytestUnknownMarkWarning` for
`error_path` because the split between `pytest.ini` and `conftest.py` is
non-standard. Per pytest docs, all markers should be declared in `pytest.ini`
(or `pyproject.toml`).

## Motivation

Move the `error_path` marker declaration to `pytest.ini` and remove the
`pytest_configure` workaround from `conftest.py`. One-line change in each file.
