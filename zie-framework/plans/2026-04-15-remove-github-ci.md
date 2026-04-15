---
approved: true
approved_at: 2026-04-15
backlog: backlog/remove-github-ci.md
---

# Remove GitHub CI — Implementation Plan

**Goal:** Delete all GitHub CI files and their dedicated test files; keep local Makefile targets intact.
**Architecture:** Pure deletion — remove `.github/` directory and CI-specific tests, verify remaining test suite passes.
**Tech Stack:** Bash (rm), pytest (verification)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Delete | `.github/workflows/ci.yml` | CI pipeline definition |
| Delete | `.github/workflows/release-provenance.yml` | SLSA provenance workflow |
| Delete | `.github/dependabot.yml` | Dependabot config |
| Delete | `.github/` directory | Container for above (empty after deletions) |
| Delete | `tests/unit/test_ci_workflow.py` | Tests that validate ci.yml structure |
| Delete | `tests/unit/test_ci_config.py` | Tests that read ci.yml directly |

---

## Task 1: Delete CI files and directory

**Acceptance Criteria:**
- `.github/` directory does not exist
- `ls .github/` returns error

**Files:**
- Delete: `.github/` (entire directory)

- [ ] **Step 1: Delete all CI files and directory**
  ```bash
  rm -rf .github/
  ```
  Verify: `ls .github/ 2>&1 | grep -q "No such file"` — must succeed

- [ ] **Step 2: Verify no other files reference .github paths**
  ```bash
  grep -r "\.github" tests/ --include="*.py" | grep -v "worktree" | grep -v ".pyc"
  ```
  Expected: no matches (archived references in `zie-framework/archive/` are acceptable)

## Task 2: Delete CI-specific test files

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `test_ci_workflow.py` and `test_ci_config.py` do not exist
- No other test files import from either deleted module
- `make test-unit` passes with both files removed

**Files:**
- Delete: `tests/unit/test_ci_workflow.py`
- Delete: `tests/unit/test_ci_config.py`

- [ ] **Step 1: Delete CI test files**
  ```bash
  rm tests/unit/test_ci_workflow.py tests/unit/test_ci_config.py
  ```
  Verify: `test -f tests/unit/test_ci_workflow.py && echo "FAIL" || echo "OK"` — must print OK

- [ ] **Step 2: Run test suite**
  ```bash
  make test-unit
  ```
  Must PASS — no import errors from removed modules

- [ ] **Step 3: Run lint**
  ```bash
  make lint
  ```
  Must PASS