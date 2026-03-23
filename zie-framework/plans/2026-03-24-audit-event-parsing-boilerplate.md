---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-event-parsing-boilerplate.md
spec: specs/2026-03-24-audit-event-parsing-boilerplate-design.md
---

# Event Parsing Boilerplate Deduplication — Implementation Plan

**Goal:** Add a `read_event()` helper to `hooks/utils.py` and replace the seven inline `json.loads(sys.stdin.read())` / `except Exception: sys.exit(0)` blocks across all hook files with a single `event = read_event()` call each.
**Architecture:** `read_event()` is a pure function added to the existing `utils.py` shared library. Each hook gains a one-line replacement. Behaviour is identical: stdin is consumed once, any parse failure exits with code 0. The `safety-check.py` `exit(2)` block logic is unaffected — that path is only reached after successful parsing.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add `read_event()` function; add `import json` |
| Modify | `hooks/auto-test.py` | Replace inline parse block with `event = read_event()` |
| Modify | `hooks/intent-detect.py` | Replace inline parse block with `event = read_event()` |
| Modify | `hooks/safety-check.py` | Replace inline parse block with `event = read_event()` |
| Modify | `hooks/session-cleanup.py` | Replace inline parse block with `event = read_event()` |
| Modify | `hooks/session-learn.py` | Replace inline parse block with `event = read_event()` |
| Modify | `hooks/session-resume.py` | Replace inline parse block with `event = read_event()` |
| Modify | `hooks/wip-checkpoint.py` | Replace inline parse block with `event = read_event()` |
| Modify | `tests/unit/test_utils.py` | Add tests for `read_event()` |

## Task 1: Add read_event() to utils.py

**Acceptance Criteria:**
- `hooks/utils.py` exports a `read_event()` function
- `read_event()` returns a `dict` parsed from stdin on success
- `read_event()` calls `sys.exit(0)` on any exception (invalid JSON, empty stdin, etc.)
- `import json` is present in `utils.py` imports
- All existing `test_utils.py` tests still pass

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing tests (RED)**
  Add to `tests/unit/test_utils.py`:

  ```python
  from utils import parse_roadmap_now, project_tmp_path, read_event
  import json
  from unittest.mock import patch

  class TestReadEvent:
      def test_valid_json_returns_dict(self):
          payload = json.dumps({"tool": "Write", "input": {}})
          with patch("sys.stdin") as mock_stdin:
              mock_stdin.read.return_value = payload
              result = read_event()
          assert result == {"tool": "Write", "input": {}}

      def test_invalid_json_exits_zero(self):
          with patch("sys.stdin") as mock_stdin:
              mock_stdin.read.return_value = "not-json"
              with pytest.raises(SystemExit) as exc:
                  read_event()
          assert exc.value.code == 0

      def test_empty_stdin_exits_zero(self):
          with patch("sys.stdin") as mock_stdin:
              mock_stdin.read.return_value = ""
              with pytest.raises(SystemExit) as exc:
                  read_event()
          assert exc.value.code == 0
  ```

  Run: `make test-unit` — must FAIL (ImportError: cannot import `read_event`)

- [ ] **Step 2: Implement (GREEN)**
  In `hooks/utils.py`, add `import json` to the top-level imports and append:

  ```python
  def read_event() -> dict:
      """Read and parse the hook event from stdin.

      Exits with code 0 on any parse failure — hooks must never crash.
      """
      try:
          return json.loads(sys.stdin.read())
      except Exception:
          sys.exit(0)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm `sys` was already imported in `utils.py` (it was — used by no existing function but present). No duplicate import needed.
  Run: `make test-unit` — still PASS

## Task 2: Replace inline parse blocks in all 7 hooks

**Acceptance Criteria:**
- None of the 7 hook files contain the inline `try: event = json.loads(sys.stdin.read()) / except Exception: sys.exit(0)` pattern
- Each hook imports `read_event` from `utils` and calls `event = read_event()`
- All existing hook unit tests pass unchanged
- `safety-check.py` `exit(2)` block logic is untouched

**Files:**
- Modify: `hooks/auto-test.py`
- Modify: `hooks/intent-detect.py`
- Modify: `hooks/safety-check.py`
- Modify: `hooks/session-cleanup.py`
- Modify: `hooks/session-learn.py`
- Modify: `hooks/session-resume.py`
- Modify: `hooks/wip-checkpoint.py`

- [ ] **Step 1: Write failing tests (RED)**
  Existing hook tests that mock stdin already implicitly test this path. No new test file needed. Confirm existing tests pass before changes as baseline.
  Run: `make test-unit` — must PASS (baseline)

- [ ] **Step 2: Implement (GREEN)**
  In each of the 7 hook files:
  1. Add `read_event` to the existing `from utils import ...` line (or add the import if absent)
  2. Replace:
     ```python
     try:
         event = json.loads(sys.stdin.read())
     except Exception:
         sys.exit(0)
     ```
     with:
     ```python
     event = read_event()
     ```
  3. Remove the now-unused `json.loads` call (keep `import json` only if the hook uses `json` elsewhere)

  Note for `auto-test.py`: the `read_event()` call goes inside the `if __name__ == "__main__":` block, matching the original placement.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Grep for remaining `json.loads(sys.stdin.read())` across `hooks/` — must return empty.
  Remove any `import json` lines in hook files where `json` is no longer used after the refactor.
  Run: `make test-unit` — still PASS
