---
slug: audit-subagent-stop-atomic
status: approved
approved: true
date: 2026-04-01
---

# Plan: Atomic Append for subagent-stop.py

## Overview

Replace the bare `open(log_file, "a")` append in `hooks/subagent-stop.py` with
the `atomic_write` pattern from `hooks/utils.py`. Eliminates race condition
under concurrent subagent sessions and aligns with hook suite convention.

Spec: `zie-framework/specs/2026-04-01-audit-subagent-stop-atomic-design.md`

---

## Tasks

### Task 1 — Write failing unit tests (RED)

Create `tests/unit/test_subagent_stop_atomic.py` with four tests:

| ID | Test name | What it asserts |
|----|-----------|----------------|
| T1 | `test_first_write_creates_file` | Absent log file is created; line present |
| T2 | `test_second_write_appends` | Second invocation appends; two lines, correct order |
| T3 | `test_concurrent_writes_no_interleaving` | Two threads write simultaneously; both lines present |
| T4 | `test_atomic_write_error_exits_zero` | `atomic_write` raising does not cause non-zero exit |

Run `make test-unit` — confirm RED (4 failures).

---

### Task 2 — Implement the fix (GREEN)

**File:** `hooks/subagent-stop.py`

**Add import:**

```python
from datetime import datetime
from utils import atomic_write
```

**Replace the bare append block:**

```python
# BEFORE
with open(log_file, "a") as f:
    f.write(line + "\n")
```

```python
# AFTER
existing = ""
if os.path.exists(log_file):
    with open(log_file, "r") as f:
        existing = f.read()
atomic_write(log_file, existing + line + "\n")
```

No other changes.

Run `make test-unit` — confirm GREEN (4 tests pass).

---

### Task 3 — Refactor / cleanup

- Confirm `open(log_file, "a")` no longer appears in `hooks/subagent-stop.py`.
- Confirm `atomic_write` import is present.
- Run `make test-ci` — no regressions.

---

## Test Strategy

All four tests are **unit tests** — fast, isolated, no I/O against real Claude
sessions. They use `tmp_path` (pytest fixture) for the log file location and
`unittest.mock.patch` to inject faults for T4.

### Runner

```bash
make test-unit   # RED check after Task 1
make test-unit   # GREEN check after Task 2
make test-ci     # full suite after Task 3
```

---

## Rollout

1. No configuration changes required.
2. No migration of existing `subagent-log.md` content — `atomic_write` reads
   the file first, so existing entries are preserved.
3. The `atomic_write` helper is already in production across other hooks.
4. Deploy by committing `hooks/subagent-stop.py` and
   `tests/unit/test_subagent_stop_atomic.py` together.
5. `make test-ci` must be green before merge.

---

## Acceptance Criteria

- [ ] `hooks/subagent-stop.py` no longer contains `open(log_file, "a")`.
- [ ] `atomic_write` is imported and used for the append.
- [ ] All four unit tests pass under `make test-unit`.
- [ ] `make test-ci` passes with no regression.
