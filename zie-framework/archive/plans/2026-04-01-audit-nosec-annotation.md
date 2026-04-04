---
slug: audit-nosec-annotation
status: approved
approved: true
date: 2026-04-01
---

# Plan: Document nosec B310 Justification in utils.py

## Overview

Replace the bare `# nosec B310` comment on `utils.py:416` with a self-explaining
justification comment. One-character edit to a comment — no functional changes,
no tests required.

**Spec:** `zie-framework/specs/2026-04-01-audit-nosec-annotation-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | `utils.py` line 416 contains `nosec B310` AND a justification comment |
| AC-2 | The justification mentions "https://" or "validated by caller" |
| AC-3 | `make test-ci` exits 0 |

---

## Tasks

### Task 1 — Update comment

**File:** `hooks/utils.py`

**Before (line 416):**
```python
    urllib.request.urlopen(req, timeout=timeout)  # nosec B310
```

**After:**
```python
    urllib.request.urlopen(req, timeout=timeout)  # nosec B310 — URL validated as https:// by caller before reaching this function
```

---

### Task 2 — Verify + test gate

```bash
grep -n 'nosec B310' hooks/utils.py
make test-ci
```

grep must show the updated comment; `make test-ci` must exit 0.

---

## Test Strategy

No new tests — comment-only change. Correctness criterion: grep confirms both
`nosec B310` and justification text present on the same line.

---

## Rollout

1. Apply str_replace (Task 1).
2. Run grep + `make test-ci` (Task 2).
3. Mark ROADMAP Done.
