---
approved: true
approved_at: 2026-03-24
backlog: backlog/security-path-traversal.md
spec: specs/2026-03-24-security-path-traversal-design.md
---

# Security: Path Traversal Fix in input-sanitizer.py — Implementation Plan

**Goal:** Replace the `startswith()` string-prefix boundary check with `Path.is_relative_to()` to eliminate the false-negative for paths like `/home/user-evil/` when cwd is `/home/user`. Add three tests covering the new edge cases.
**Architecture:** Single-line fix in `hooks/input-sanitizer.py:58` + three new test methods in `tests/unit/test_input_sanitizer.py`.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_input_sanitizer.py` | Add 3 failing tests for the edge cases |
| Modify | `hooks/input-sanitizer.py` | Replace `startswith()` with `is_relative_to()` at line 58 |

---

## Task 1: Path traversal edge cases — `tests/unit/test_input_sanitizer.py`

**Acceptance Criteria:**
- `test_path_traversal_user_evil_prefix` — `file_path="../user-evil/evil.py"` with `CLAUDE_CWD=/home/user` exits 0, stdout empty, `"escapes cwd"` in stderr
- `test_path_nul_byte_rejected` — `file_path="foo\x00bar.py"` exits 0, no crash, stdout empty or valid JSON
- `test_path_with_symlink_outside_cwd` — symlink in tmpdir pointing to `/etc`, `file_path="link/passwd"` exits 0, stdout empty

**Files:**
- Modify: `tests/unit/test_input_sanitizer.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_input_sanitizer.py, inside a new class:

  class TestPathTraversalEdgeCases:
      def test_path_traversal_user_evil_prefix(self, tmp_path):
          """startswith() false-negative: /home/user-evil/ passes the old check.

          With is_relative_to() this must be rejected — hook exits 0, stdout
          empty, stderr contains 'escapes cwd'.
          """
          # Simulate cwd=/home/user by using a real tmpdir whose name ends in
          # a prefix that a sibling dir would share, e.g. tmp_path = /tmp/user
          # The key is that ../user-evil resolves to a path outside tmp_path.
          r = run_hook("Write", {"file_path": "../user-evil/evil.py"}, cwd_override=str(tmp_path))
          assert r.returncode == 0
          assert r.stdout.strip() == ""
          assert "escapes cwd" in r.stderr

      def test_path_nul_byte_rejected(self, tmp_path):
          """NUL byte in file_path must not crash the hook.

          Python's Path() raises ValueError on NUL bytes; the inner except
          block catches it and exits 0.
          """
          r = run_hook("Write", {"file_path": "foo\x00bar.py"}, cwd_override=str(tmp_path))
          assert r.returncode == 0
          # Must not crash — stdout is empty (no rewrite) or valid JSON
          if r.stdout.strip():
              json.loads(r.stdout)  # raises if not valid JSON

      def test_path_with_symlink_outside_cwd(self, tmp_path):
          """Symlink inside cwd pointing outside cwd must be rejected.

          .resolve() follows the symlink to its real path; is_relative_to()
          then rejects it because the real path is outside tmp_path.
          """
          # Create tmpdir/link -> /etc
          link = tmp_path / "link"
          link.symlink_to("/etc")
          r = run_hook("Write", {"file_path": "link/passwd"}, cwd_override=str(tmp_path))
          assert r.returncode == 0
          assert r.stdout.strip() == ""
  ```

  Run: `make test-unit` — must **FAIL**

  `test_path_traversal_user_evil_prefix` fails because the current `startswith()` check at line 58 returns `True` for `../user-evil/` (the resolved path shares the string prefix of `tmp_path`), so the hook rewrites the path instead of rejecting it — stdout is non-empty.

  `test_path_nul_byte_rejected` and `test_path_with_symlink_outside_cwd` may pass or fail depending on the Python version behaviour, but RED is declared when at least `test_path_traversal_user_evil_prefix` fails.

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/input-sanitizer.py — line 58

  # BEFORE:
  if not str(abs_path).startswith(str(cwd)):

  # AFTER:
  if not abs_path.is_relative_to(cwd):
  ```

  `Path.is_relative_to()` compares path components, not string characters.
  `/home/user-evil/file.txt` is correctly **not** relative to `/home/user` because
  `user-evil` != `user` at the component level.

  Run: `make test-unit` — must **PASS**

---

- [ ] **Step 3: Refactor**

  Verify that all pre-existing traversal tests still pass with the new check:
  - `test_traversal_path_produces_no_output` (`../../etc/passwd`) — still rejected ✓
  - `test_traversal_path_logs_stderr_warning` — stderr warning still emitted ✓
  - `test_relative_path_resolved_to_absolute` — valid relative path still rewritten ✓

  No further code changes are needed. The comment on lines 56–58 of
  `hooks/input-sanitizer.py` should be updated to reflect the new method:

  ```python
  # BEFORE comment:
  # Boundary check — must stay inside project root.
  # Both sides are .resolve()-ed (symlinks followed) for accurate prefix check.

  # AFTER comment:
  # Boundary check — must stay inside project root.
  # Both sides are .resolve()-ed (symlinks followed) before is_relative_to()
  # comparison, which checks path components (not string prefix).
  ```

  Run: `make test-unit` — still **PASS**
  Run: `make lint` — exits 0

---

**Commit:** `git add hooks/input-sanitizer.py tests/unit/test_input_sanitizer.py && git commit -m "fix: security-path-traversal — replace startswith() with is_relative_to() in input-sanitizer"`
