# Implementation Plan: task-gate-suppress-advisory

**Slug:** task-gate-suppress-advisory
**Spec:** `zie-framework/specs/2026-04-04-task-gate-suppress-advisory-design.md`
**Date:** 2026-04-04

## Steps

### 1. Remove the advisory print — `hooks/task-completed-gate.py`

**File:** `hooks/task-completed-gate.py`

Remove line 118:
```python
print("[zie-framework] task-completed-gate: advisory task — gate skipped")
```

Leave `sys.exit(0)` on the next line untouched.

### 2. Update the test — `tests/unit/test_hooks_task_completed_gate.py`

**File:** `tests/unit/test_hooks_task_completed_gate.py`

Line 68 — change:
```python
assert "advisory" in r.stdout.lower()
```
to:
```python
assert r.stdout == ""
```

### 3. Verify

```bash
make test-fast
```

Both changes should land green with no other test failures.

## Checklist

- [ ] Hook line removed
- [ ] Test assertion updated
- [ ] `make test-fast` green
