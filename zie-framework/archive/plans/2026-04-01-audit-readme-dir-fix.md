---
slug: audit-readme-dir-fix
status: approved
approved: true
date: 2026-04-01
---

# Plan: Fix Doubled Path Component in README.md Directory Structure

## Overview

Single str_replace in `README.md` to fix `project/context.md` →
`context.md` inside the `project/` directory listing. The doubled component
causes the path to read as `zie-framework/project/project/context.md` which
does not exist on disk.

**Spec:** `zie-framework/specs/2026-04-01-audit-readme-dir-fix-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | `README.md` does not contain `project/context.md` under the `project/` directory listing |
| AC-2 | `README.md` contains `context.md` (without the doubled `project/` prefix) in that position |
| AC-3 | `make test-fast` exits 0 — no tests broken |

---

## Tasks

### Task 1 — Apply fix

**File:** `README.md`

**Before:**
```
│   │   └── project/context.md  # ADR log (append-only)
```

**After:**
```
│   │   └── context.md          # spokes: context and session state
```

---

### Task 2 — Verify

```bash
grep -n 'project/context' README.md && echo "FAIL: doubled path still present" || echo "OK"
grep -n 'context.md' README.md
```

First grep must exit non-zero (no match). Second must show the corrected line.

---

### Task 3 — Test gate

```bash
make test-fast
```

Must exit 0.

---

## Test Strategy

No new tests — documentation-only change. Verification is a grep confirmation.

---

## Rollout

1. Apply str_replace (Task 1).
2. Run verification greps (Task 2).
3. Run `make test-fast` (Task 3).
4. Mark ROADMAP Done.
