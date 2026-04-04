---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-cwd-init-boilerplate.md
spec: specs/2026-03-24-audit-cwd-init-boilerplate-design.md
---

# CLAUDE_CWD Initialization Boilerplate Deduplication — Implementation Plan

**Goal:** Add a `get_cwd()` helper to `hooks/utils.py` and replace the six inline `Path(os.environ.get("CLAUDE_CWD", os.getcwd()))` expressions with `cwd = get_cwd()`.
**Architecture:** `get_cwd()` is a pure function added to `utils.py`. It centralises the `CLAUDE_CWD` contract in one place. `safety-check.py` does not use `CLAUDE_CWD` and is excluded. `import os` is added to `utils.py` since it is currently absent. Behaviour is identical to the inline form.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add `get_cwd()` function; add `import os` |
| Modify | `hooks/auto-test.py` | Replace inline expression with `cwd = get_cwd()` |
| Modify | `hooks/intent-detect.py` | Replace inline expression with `cwd = get_cwd()` |
| Modify | `hooks/session-cleanup.py` | Replace inline expression with `cwd = get_cwd()` |
| Modify | `hooks/session-learn.py` | Replace inline expression with `cwd = get_cwd()` |
| Modify | `hooks/session-resume.py` | Replace inline expression with `cwd = get_cwd()` |
| Modify | `hooks/wip-checkpoint.py` | Replace inline expression with `cwd = get_cwd()` |
| Modify | `tests/unit/test_utils.py` | Add tests for `get_cwd()` |

## Task 1: Add get_cwd() to utils.py

**Acceptance Criteria:**
- `hooks/utils.py` exports a `get_cwd()` function
- When `CLAUDE_CWD` is set, `get_cwd()` returns `Path(os.environ["CLAUDE_CWD"])`
- When `CLAUDE_CWD` is unset, `get_cwd()` returns `Path(os.getcwd())`
- `import os` is present in `utils.py`
- All existing `test_utils.py` tests still pass

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing tests (RED)**
  Add to `tests/unit/test_utils.py`:

  ```python
  from utils import parse_roadmap_now, project_tmp_path, get_cwd
  import os
  from pathlib import Path

  class TestGetCwd:
      def test_returns_claude_cwd_when_set(self, monkeypatch, tmp_path):
          monkeypatch.setenv("CLAUDE_CWD", str(tmp_path))
          result = get_cwd()
          assert result == Path(str(tmp_path))

      def test_returns_getcwd_when_env_unset(self, monkeypatch):
          monkeypatch.delenv("CLAUDE_CWD", raising=False)
          result = get_cwd()
          assert result == Path(os.getcwd())

      def test_returns_path_object(self, monkeypatch, tmp_path):
          monkeypatch.setenv("CLAUDE_CWD", str(tmp_path))
          assert isinstance(get_cwd(), Path)
  ```

  Run: `make test-unit` — must FAIL (ImportError: cannot import `get_cwd`)

- [ ] **Step 2: Implement (GREEN)**
  In `hooks/utils.py`, add `import os` to the top-level imports and append:

  ```python
  def get_cwd() -> Path:
      """Return the working directory for the current Claude Code session.

      Prefers CLAUDE_CWD env var (set by Claude Code) over os.getcwd().
      """
      return Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm `Path` is already imported in `utils.py` (it is — used by `parse_roadmap_now` and `project_tmp_path`). No duplicate import needed.
  Run: `make test-unit` — still PASS

## Task 2: Replace inline CLAUDE_CWD expressions in 6 hooks

**Acceptance Criteria:**
- None of the 6 hook files contain the inline `Path(os.environ.get("CLAUDE_CWD", os.getcwd()))` expression
- Each hook imports `get_cwd` from `utils` and calls `cwd = get_cwd()`
- All existing hook unit tests pass unchanged
- `safety-check.py` is not changed

**Files:**
- Modify: `hooks/auto-test.py`
- Modify: `hooks/intent-detect.py`
- Modify: `hooks/session-cleanup.py`
- Modify: `hooks/session-learn.py`
- Modify: `hooks/session-resume.py`
- Modify: `hooks/wip-checkpoint.py`

- [ ] **Step 1: Write failing tests (RED)**
  Existing hook tests already cover the `cwd` usage paths. Confirm all pass as baseline before changes.
  Run: `make test-unit` — must PASS (baseline)

- [ ] **Step 2: Implement (GREEN)**
  In each of the 6 hook files:
  1. Add `get_cwd` to the existing `from utils import ...` line
  2. Replace:
     ```python
     cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
     ```
     with:
     ```python
     cwd = get_cwd()
     ```
  3. If `os` is no longer used elsewhere in the hook after this replacement, remove `import os`

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Grep for remaining `os.environ.get("CLAUDE_CWD"` across `hooks/` — must return empty.
  Run: `make test-unit` — still PASS
