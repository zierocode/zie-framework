---
slug: audit-pytest-markers-consolidate
status: approved
approved: true
date: 2026-04-01
---

# Plan: Move `error_path` Marker Declaration to pytest.ini

## Overview

Move the `error_path` pytest marker from `conftest.py::pytest_configure` into
`pytest.ini`. Remove the `pytest_configure` workaround. One-line addition to
`pytest.ini`, one block removal from `conftest.py`. Enables `--strict-markers`
without `PytestUnknownMarkWarning`.

**Spec:** `zie-framework/specs/2026-04-01-audit-pytest-markers-consolidate-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | `pytest.ini` declares both `integration` and `error_path` markers |
| AC-2 | `conftest.py` no longer contains `pytest_configure` marker registration |
| AC-3 | `pytest --strict-markers tests/unit/` exits 0 |
| AC-4 | `make test-ci` exits 0 |

---

## Tasks

### Task 1 — Add `error_path` to pytest.ini

**File:** `pytest.ini`

**Before:**
```ini
[pytest]
markers =
    integration: marks tests as integration tests (run with make test-int)
```

**After:**
```ini
[pytest]
markers =
    integration: marks tests as integration tests (run with make test-int)
    error_path: marks tests that exercise hook error paths (missing input, malformed data, subprocess failure)
```

---

### Task 2 — Remove `pytest_configure` from conftest.py

**File:** `tests/conftest.py`

**Before:**
```python
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "error_path: marks tests that exercise hook error paths (missing input, malformed data, subprocess failure)",
    )
```

**After:** (delete the entire function — 5 lines)

---

### Task 3 — Verify + full suite gate

```bash
pytest --strict-markers tests/unit/ -q 2>&1 | tail -5
make test-ci
```

Both must exit 0.

---

## Test Strategy

No new tests — configuration-only change. Correctness criterion:
- `pytest --strict-markers` exits 0 (AC-3)
- Existing `@pytest.mark.error_path` decorated tests still collected (AC-4)

---

## Rollout

1. Add `error_path` line to pytest.ini (Task 1).
2. Remove `pytest_configure` block from conftest.py (Task 2).
3. Run `pytest --strict-markers` + `make test-ci` (Task 3).
4. Mark ROADMAP Done.
