---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-filepath-cwd-validation.md
spec: specs/2026-03-24-audit-filepath-cwd-validation-design.md
---

# file_path CWD Boundary Validation — Implementation Plan

**Goal:** Validate that `file_path` from the hook event resolves within the project root before use, exiting cleanly on out-of-bounds paths.
**Architecture:** After `changed = Path(file_path)` on line 89 of `auto-test.py`, resolve both `changed` and `cwd` with `.resolve()` and call `changed.is_relative_to(cwd_resolved)`. On failure, `sys.exit(0)` — silent, non-blocking. This prevents `/etc/passwd`, `../` traversal paths, and `/tmp` paths from reaching `changed.stem`, `find_matching_test()`, or log output.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/auto-test.py` | Add cwd boundary check after `changed = Path(file_path)` |
| Modify | `tests/unit/test_hooks_auto_test.py` | Add out-of-bounds path test cases |

---

## Task 1: Reject file_path Outside Project Root

**Acceptance Criteria:**
- `file_path = "/etc/passwd"` causes hook to exit 0 with no output
- `file_path = "/tmp/foo.py"` (outside cwd) causes hook to exit 0 with no output
- `file_path` using `../` traversal to escape cwd causes hook to exit 0 with no output
- A valid in-project path still proceeds normally
- Empty `file_path` is still caught by the existing early-exit guard (unchanged)

**Files:**
- Modify: `hooks/auto-test.py`
- Modify: `tests/unit/test_hooks_auto_test.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_hooks_auto_test.py

  class TestAutoTestFilePathCwdValidation:
      """file_path must be resolved and validated within cwd before use."""

      def test_absolute_path_outside_cwd_exits_zero(self, tmp_path):
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": "/etc/passwd"}},
              tmp_cwd=cwd,
          )
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_tmp_path_outside_cwd_exits_zero(self, tmp_path):
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": "/tmp/malicious.py"}},
              tmp_cwd=cwd,
          )
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_dotdot_traversal_outside_cwd_exits_zero(self, tmp_path):
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          # Construct a path that traverses outside cwd
          escaped = str(cwd) + "/../../etc/passwd"
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": escaped}},
              tmp_cwd=cwd,
          )
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_path_inside_cwd_proceeds(self, tmp_path):
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          # A path inside cwd — hook should proceed past the validation check
          # (it will exit 0 for other reasons: pytest not found or no tests, but NOT due to boundary check)
          inside_path = str(cwd / "hooks" / "utils.py")
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": inside_path}},
              tmp_cwd=cwd,
          )
          # The hook did not silently block it (returncode 0 is fine for other reasons)
          # Key: no "boundary" or path-leak output
          assert r.returncode == 0
          assert "/etc/passwd" not in r.stdout
          assert "/etc/passwd" not in r.stderr

      def test_out_of_bounds_path_not_leaked_to_output(self, tmp_path):
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
          r = run_hook(
              {"tool_name": "Edit", "tool_input": {"file_path": "/etc/shadow"}},
              tmp_cwd=cwd,
          )
          assert "/etc/shadow" not in r.stdout
          assert "/etc/shadow" not in r.stderr
  ```

  Run: `make test-unit` — must FAIL (`test_absolute_path_outside_cwd_exits_zero` and variants fail because the hook currently proceeds with `/etc/passwd` and `changed.stem = "passwd"` reaches `find_matching_test()` and potentially log output)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # In hooks/auto-test.py, replace line 89:
  # BEFORE:
  changed = Path(file_path)

  # AFTER:
  changed = Path(file_path).resolve()
  cwd_resolved = cwd.resolve()
  if not changed.is_relative_to(cwd_resolved):
      sys.exit(0)
  ```

  These three lines replace the single `changed = Path(file_path)` line.
  All downstream uses of `changed` (e.g. `changed.stem`, `find_matching_test(changed, ...)`)
  now receive a resolved, in-bounds path.

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  `Path.is_relative_to()` was added in Python 3.9. The project targets Python 3.x
  (see CLAUDE.md). Verify the minimum version in use:

  ```bash
  python3 --version  # must be >= 3.9
  ```

  If the project must support Python 3.8, replace with the equivalent:
  ```python
  try:
      changed.relative_to(cwd_resolved)
  except ValueError:
      sys.exit(0)
  ```

  For Python >= 3.9 (expected), `is_relative_to` is cleaner — keep it.

  The `cwd_resolved` variable is local to this block. No helper needed (YAGNI).

  Run: `make test-unit` — still PASS

---

**Commit:** `git add hooks/auto-test.py tests/unit/test_hooks_auto_test.py && git commit -m "fix: audit-filepath-cwd-validation — validate file_path within cwd before use"`
