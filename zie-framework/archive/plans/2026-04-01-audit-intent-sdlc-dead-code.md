---
slug: audit-intent-sdlc-dead-code
status: approved
approved: true
date: 2026-04-01
---

# Plan: Remove Dead `__main__` Guard from intent-sdlc.py

## Overview

Delete the two dead lines `if __name__ == "__main__": pass` at the bottom of
`hooks/intent-sdlc.py` (lines 335–336). All hook logic executes at module
top level — the `__main__` guard is unreachable and creates a misleading
inconsistency with `auto-test.py` and `task-completed-gate.py`.

**Spec:** `zie-framework/specs/2026-04-01-audit-intent-sdlc-dead-code-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | `hooks/intent-sdlc.py` does not contain `if __name__ == "__main__": pass` |
| AC-2 | Existing test suite passes; `make test-ci` exits 0 |

---

## Tasks

### Task 1 — Verify dead code (pre-condition)

```bash
grep -n '__name__.*__main__' hooks/intent-sdlc.py
```

Expected output: `335:if __name__ == "__main__":` — confirms the dead block.

---

### Task 2 — Remove dead lines

**File:** `hooks/intent-sdlc.py`

**Before (lines 333–336, end of file):**
```python


if __name__ == "__main__":
    pass
```

**After:**
```python
```

(Remove the two blank lines + the two-line dead block; file ends after the
previous `sys.exit(0)` or last meaningful statement.)

---

### Task 3 — Verify removal + full suite gate

```bash
grep '__name__.*__main__' hooks/intent-sdlc.py && echo "FAIL: dead code still present" || echo "OK: removed"
make test-ci
```

Both must succeed (grep exits non-zero = OK; make test-ci exits 0).

---

## Test Strategy

No new tests required — this is dead code removal. Correctness criterion:
- grep confirms absence (AC-1)
- Existing suite continues to pass (AC-2)

---

## Rollout

1. Run pre-condition grep (Task 1) — confirm dead block present.
2. Apply str_replace to remove block (Task 2).
3. Run verification grep + `make test-ci` (Task 3) — no regression.
4. Mark ROADMAP Done.
