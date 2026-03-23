---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-gitignore-gaps.md
spec: specs/2026-03-24-audit-gitignore-gaps-design.md
---

# .gitignore Gaps — Implementation Plan

**Goal:** Add `.pytest_cache/` and `zie-framework/evidence/` to the root `.gitignore` to prevent accidental commits of test cache noise and local audit data.
**Architecture:** Two-line append to the existing four-line `.gitignore`. No code or config changes. The `evidence/` entry is the higher-priority fix — audit data is local-only by design. The `.pytest_cache/` entry matches at any subdirectory depth (no leading `/`).
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `.gitignore` | Append .pytest_cache/ and zie-framework/evidence/ entries |

## Task 1: Add missing entries to .gitignore

**Acceptance Criteria:**
- `.gitignore` contains `.pytest_cache/` entry
- `.gitignore` contains `zie-framework/evidence/` entry
- The four existing entries (`__pycache__/`, `*.pyc`, `.DS_Store`, `/tmp/zie-framework-*`) are unchanged
- `git ls-files zie-framework/evidence/` returns empty (no tracked files would be newly ignored)
- `make test-unit` passes

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — config file change. Verified manually by reading `.gitignore` and confirming entries are absent before fix, present after.
  Run: `make test-unit` — existing tests pass (baseline)

- [ ] **Step 2: Implement (GREEN)**
  Append to `.gitignore`:

  ```text
  .pytest_cache/
  zie-framework/evidence/
  ```

  Final `.gitignore`:

  ```text
  __pycache__/
  *.pyc
  .DS_Store
  /tmp/zie-framework-*
  .pytest_cache/
  zie-framework/evidence/
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Run `git ls-files zie-framework/evidence/` — confirm empty (no newly-ignored tracked files).
  Run `git check-ignore -v .pytest_cache` — confirm the new entry matches.
  Run: `make test-unit` — still PASS
