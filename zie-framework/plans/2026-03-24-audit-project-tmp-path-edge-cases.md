---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-project-tmp-path-edge-cases.md
spec: specs/2026-03-24-audit-project-tmp-path-edge-cases-design.md
---

# project_tmp_path() — Edge Case Tests for Pathological Input Names — Implementation Plan

**Goal:** Add a `TestProjectTmpPathEdgeCases` class to `test_utils.py` that documents and verifies `project_tmp_path()` behaviour for unicode, emoji, leading-dash, very-long, path-traversal, and dot-only project names.
**Architecture:** Pure test addition. Each test calls `project_tmp_path()` directly with a pathological input and asserts the returned `Path` is valid and matches the expected sanitised form produced by `re.sub(r'[^a-zA-Z0-9]', '-', project)`. If any test reveals an unsafe or OS-breaking output, `hooks/utils.py` is patched (e.g. adding a length cap) before merge.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_utils.py` | Add class `TestProjectTmpPathEdgeCases` with 6 test methods |
| Modify (if needed) | `hooks/utils.py` | Harden `project_tmp_path()` if tests expose unsafe output |

---

## Task 1: Add TestProjectTmpPathEdgeCases to test_utils.py

**Acceptance Criteria:**
- `test_unicode_project_name`: path contains only ASCII chars (accented letters replaced by `-`)
- `test_emoji_project_name`: emoji replaced by `-`, result is valid `Path`
- `test_leading_dash_project_name`: documents that leading dash produces `--` prefix; asserts exact path
- `test_very_long_project_name`: documents that no truncation occurs; asserts `len(result.name) > 255`; includes docstring warning about OS write-time `OSError`
- `test_path_traversal_attempt`: `..` and `/` are replaced by `-`; result does not contain `..` or a bare `/` after `/tmp/`
- `test_dot_only_project_name`: `.` is replaced by `-`; result is valid and contains no unescaped dot segment

**Files:**
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append the new class. Tests are RED because the class does not yet exist in the file:

  ```python
  class TestProjectTmpPathEdgeCases:
      """Contract tests for project_tmp_path() with pathological project names.

      These tests document known behaviour (including known gaps like no length cap).
      If implementation changes, update assertions AND the spec.
      """

      def test_unicode_project_name(self):
          # Accented chars are outside [a-zA-Z0-9] — replaced with '-'
          result = project_tmp_path("last-test", "mon-projet-café")
          result_str = str(result)
          # Result must be ASCII-only
          assert result_str.isascii(), f"Expected ASCII path, got: {result_str}"
          assert isinstance(result, Path)
          # 'é' → '-', so 'café' → 'caf-'
          assert result_str == "/tmp/zie-mon-projet-caf--last-test"

      def test_emoji_project_name(self):
          # Each emoji code point is non-alphanumeric — replaced with single '-'
          result = project_tmp_path("edit-count", "my-app-\U0001F680")
          result_str = str(result)
          assert result_str.isascii(), f"Expected ASCII path, got: {result_str}"
          assert isinstance(result, Path)
          # '\U0001F680' (rocket) → '-'
          assert result_str == "/tmp/zie-my-app--edit-count"

      def test_leading_dash_project_name(self):
          # Leading '-' in project name is alphanumeric? No — '-' is not in [a-zA-Z0-9]
          # re.sub replaces '-' with '-' (no change), so '-myproject' stays '-myproject'
          # Result: /tmp/zie--myproject-last-test (leading '--' because zie- + -myproject)
          result = project_tmp_path("last-test", "-myproject")
          assert str(result) == "/tmp/zie--myproject-last-test"
          assert isinstance(result, Path)

      def test_very_long_project_name(self):
          """No truncation: name >255 chars will cause OSError at write time, not at Path construction.

          This test documents the known gap — callers must handle OSError on write.
          """
          long_name = "x" * 256
          result = project_tmp_path("edit-count", long_name)
          # Path construction does not raise
          assert isinstance(result, Path)
          # The filename component is longer than 255 chars (known gap — no truncation)
          assert len(result.name) > 255

      def test_path_traversal_attempt(self):
          # '.' and '/' are both outside [a-zA-Z0-9] — replaced with '-'
          # '../etc' → '--etc' (each char replaced individually)
          result = project_tmp_path("last-test", "../etc")
          result_str = str(result)
          # Must not contain '..' as a path component
          assert ".." not in result_str
          # Must not contain a bare '/' after the /tmp/ prefix that would escape the dir
          parts = Path(result_str).parts
          assert parts[0] == "/"
          assert parts[1] == "tmp"
          # Traversal neutralised — all dots and slashes replaced
          assert result_str == "/tmp/zie----etc-last-test"

      def test_dot_only_project_name(self):
          # '.' → '-' via re.sub
          result = project_tmp_path("x", ".")
          result_str = str(result)
          assert result_str == "/tmp/zie---x"
          assert isinstance(result, Path)
          # No unescaped dot segment
          assert "/." not in result_str
  ```

  Run: `make test-unit` — must FAIL (class not yet in file)

- [ ] **Step 2: Implement (GREEN)**

  The implementation IS adding the class above to `test_utils.py`. The `project_tmp_path()` source in `hooks/utils.py` is expected to produce exactly the values asserted. Run to confirm:

  Run: `make test-unit` — must PASS

  If any assertion fails due to a different sanitised value (e.g. emoji produces `--` instead of `-`), adjust the assertion to match actual `re.sub` output and add a comment explaining the Unicode normalization detail.

  If `test_path_traversal_attempt` reveals that `/` in the project name is NOT replaced (e.g. on a platform where `re.sub` behaves differently), fix `hooks/utils.py` by ensuring the regex covers `/`:

  ```python
  # hooks/utils.py — only change if test exposes a gap:
  safe_project = re.sub(r'[^a-zA-Z0-9]', '-', project)
  # Current regex already covers '/' and '.' — verify this is the case
  ```

- [ ] **Step 3: Refactor**

  Ensure `test_very_long_project_name` has a clear docstring (already included above) so the "known gap — no truncation" intent is visible to future maintainers. No logic cleanup needed.

  Run: `make test-unit` — still PASS
