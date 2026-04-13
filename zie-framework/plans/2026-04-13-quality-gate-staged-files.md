---
approved: true
approved_at: 2026-04-13
backlog: backlog/quality-gate-staged-files.md
spec: specs/2026-04-13-quality-gate-staged-files-design.md
---

# quality-gate: Scope Bandit Scan to Staged Files — Implementation Plan

**Goal:** Replace the repo-wide `rglob("*.py")[:20]` bandit scan in `hooks/quality-gate.py` with a staged-files-only scan using `git diff --cached --name-only --diff-filter=ACM`.

**Tech Stack:** Python 3.x, subprocess (already used in this hook), pytest

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `hooks/quality-gate.py` | Replace rglob with staged files from git diff |
| Modify | `tests/unit/test_quality_gate.py` | Update bandit tests; add staged-files and empty-staged tests |

---

## Task 1 — Replace rglob bandit scan with staged-files scan

**RED:** Write a test that:
- Mocks `subprocess.run` for both `git diff` and `bandit` calls
- Asserts bandit is called with staged Python files, not rglob files
- Asserts bandit is NOT called when no staged Python files

**File:** `tests/unit/test_quality_gate.py`

**GREEN:** In `hooks/quality-gate.py`, replace Check 3 (bandit section):

```python
# OLD: cwd.rglob("*.py")[:20]
# NEW:
result_diff = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
    capture_output=True, text=True, timeout=10, cwd=str(cwd)
)
staged_py = [
    str(cwd / f) for f in result_diff.stdout.splitlines()
    if f.endswith(".py") and not any(
        part in Path(f).parts
        for part in ("venv", ".venv", "node_modules", "__pycache__")
    )
]
if not staged_py:
    pass  # skip bandit — no staged Python files
else:
    result = subprocess.run(
        ["bandit", "-q", "-ll", "-x", ".venv,venv"] + staged_py,
        ...
    )
```

**Acceptance Criteria:**
- [ ] Bandit called with staged files only
- [ ] Empty staged list → bandit not called
- [ ] git diff failure → bandit skipped silently (try/except covers it)
- [ ] venv/.venv filter still applied

---

## Task 2 — Update + add tests

**Tests to add/update in `tests/unit/test_quality_gate.py`:**
1. `test_bandit_uses_staged_files` — verify subprocess gets staged files list
2. `test_bandit_skips_when_no_staged_py` — mock empty git diff output, assert bandit not called
3. `test_bandit_skips_on_git_diff_failure` — mock git diff raising exception, assert bandit not called

**Acceptance Criteria:**
- [ ] All 3 new tests pass
- [ ] Existing quality-gate tests still pass

---

## Estimated Risk: LOW
- Self-contained change within one hook function
- Graceful degradation already in place (try/except block)
- No new dependencies
