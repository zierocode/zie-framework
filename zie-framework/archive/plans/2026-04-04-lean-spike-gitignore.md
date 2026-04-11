---
slug: lean-spike-gitignore
spec: zie-framework/specs/2026-04-04-lean-spike-gitignore-design.md
approved: true
approved_at: 2026-04-04
created: 2026-04-04
---

# Plan: Lean Spike — Auto-gitignore spike-*/

**Goal:** Append `spike-*/` to `.gitignore` in Step 1 of `/spike` so spike
directories are never accidentally committed.

**Architecture:** Pure markdown command edit — no hook or Python changes. The
idempotency check is expressed as Claude instruction text in `commands/spike.md`
Step 1. One new test file asserts the behavior is documented correctly.

**Tech Stack:** Markdown (commands/spike.md), pytest structural tests.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/spike.md` | Add .gitignore check to Step 1 |
| Modify | `tests/unit/test_zie_spike_command.py` | Add structural tests for new behavior |

---

### Task 1 — Edit commands/spike.md Step 1

**File:** `commands/spike.md`

Replace Step 1:

```
1. **Create sandbox** — `mkdir spike-<slug>/` at repo root. All spike files live here.
```

With:

```
1. **Create sandbox** — `mkdir spike-<slug>/` at repo root. All spike files live here.
   Then ensure `spike-*/` is git-ignored:
   - Read `.gitignore` (treat as empty string if file does not exist).
   - If `spike-*/` is not already a line in `.gitignore`, append it.
   - Print: `[spike] spike-*/ added to .gitignore — spike dirs are throwaway and will not be committed.`
   - If `spike-*/` was already present, skip silently.
```

**AC check:** Step 1 text contains `spike-*/`, `.gitignore`, and `skip silently`.

---

### Task 2 — Add structural tests

<!-- depends_on: Task 1 -->

**File:** `tests/unit/test_zie_spike_command.py`

Add to the existing test file:

```python
def test_gitignore_check_in_step1():
    text = CMD.read_text()
    assert "spike-*/" in text, "Step 1 must reference spike-*/ gitignore pattern"
    assert ".gitignore" in text, "Step 1 must reference .gitignore"
    assert "skip silently" in text, "Idempotent skip must be documented"


def test_gitignore_message_present():
    text = CMD.read_text()
    assert "throwaway" in text, "User guidance that spike dirs are throwaway must be present"
    assert "will not be committed" in text or "git-ignored" in text, (
        "Step 1 must confirm spike dirs are not committed"
    )
```

---

## Verification

```bash
make lint
make test-fast
```

Both must pass with zero failures.
