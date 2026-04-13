---
approved: true
approved_at: 2026-04-13
backlog: backlog/quality-gate-staged-files.md
---

# quality-gate: Scope Bandit Scan to Staged Files Only — Design Spec

**Problem:** `hooks/quality-gate.py` currently runs `bandit` on up to 20 Python files chosen by `rglob("*.py")` from the entire repo. This scans arbitrary unrelated files that aren't part of the commit, making security warnings irrelevant to the actual change being committed.

**Approach:** Replace the full-repo rglob with `git diff --cached --name-only --diff-filter=ACM` to get staged Python files. This naturally bounds the scan to only files in the commit, eliminates the 20-file arbitrary cap (replaced by "however many .py files are staged"), and makes bandit output actionable. If `git diff` fails or no Python files are staged → skip bandit silently.

**Non-goals:** Coverage and dead-code checks are unchanged. Bandit flags and thresholds unchanged. Warn-only behavior unchanged.

**Components:**
- Modify: `hooks/quality-gate.py` — replace rglob bandit scan with `git diff --cached` staged files; handle empty/error cases gracefully
- Modify: `tests/unit/test_quality_gate.py` — update bandit scan tests; add test for empty staged list (no bandit invoked)

**Data Flow:**
1. `git commit` detected → quality gate fires
2. Run `git diff --cached --name-only --diff-filter=ACM` → parse `.py` files
3. Filter out venv/.venv/node_modules/__pycache__ as before
4. If list empty → skip bandit silently
5. If list non-empty → run `bandit -q -ll -x .venv,venv <staged_py_files>`
6. Emit warnings as before (warn-only, never blocks)

**Acceptance Criteria:**
- AC1: Bandit runs only on staged Python files, not repo-wide rglob
- AC2: Empty staged file list → bandit not invoked (no error)
- AC3: `git diff` failure → skip bandit silently, exit 0
- AC4: venv/.venv filtering still applies to staged files
- AC5: All existing quality-gate tests pass; new tests added for staged-files path
