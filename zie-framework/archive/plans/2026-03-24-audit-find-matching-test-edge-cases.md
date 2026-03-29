---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-find-matching-test-edge-cases.md
spec: specs/2026-03-24-audit-find-matching-test-edge-cases-design.md
---

# find_matching_test() — Edge Case Tests for Missing/Unusual Test Directory Structures — Implementation Plan

**Goal:** Add a `TestFindMatchingTestEdgeCases` class to `test_hooks_auto_test.py` covering missing `tests/` directory, symlinked test files, permission-denied directory, non-standard file extensions, and empty test directories — ensuring `find_matching_test()` degrades gracefully rather than crashing.
**Architecture:** Tests import `find_matching_test` directly via the existing `load_module` fixture pattern from `TestFindMatchingTest`. Each test creates a controlled filesystem state in `tmp_path`. If test #1 (missing `tests/` dir) exposes an unhandled `OSError` from `Path.rglob()` on a non-existent path, `hooks/auto-test.py` is patched with a `try/except OSError` guard before merge.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_hooks_auto_test.py` | Add class `TestFindMatchingTestEdgeCases` with 6 test methods |
| Modify (if needed) | `hooks/auto-test.py` | Wrap `tests_dir.rglob(...)` in `try/except OSError` if test #1 reveals unhandled exception |

---

## Task 1: Add TestFindMatchingTestEdgeCases to test_hooks_auto_test.py

**Acceptance Criteria:**
- `test_no_tests_directory_returns_none`: no `tests/` dir → result is `None`, no exception raised
- `test_symlinked_test_file_found`: symlink to a real test file is followed; result is the real file path
- `test_permission_denied_on_tests_dir_returns_none`: `chmod 000` on `tests/` → result is `None`, no exception; test skipped when running as root; permissions restored in teardown
- `test_non_standard_extension_not_matched_for_pytest`: `.ts` file in `tests/` not returned for pytest runner
- `test_vitest_missing_test_file_returns_none`: no `.test.ts` or `.spec.ts` → result is `None`
- `test_empty_tests_directory_returns_none`: `tests/` dir exists but is empty → result is `None`

**Files:**
- Modify: `tests/unit/test_hooks_auto_test.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append the new class. Tests are RED because the class does not yet exist:

  ```python
  class TestFindMatchingTestEdgeCases:
      """Edge case tests for find_matching_test() — unusual or degraded filesystem states."""

      @pytest.fixture
      def load_module(self):
          """Import auto-test.py without triggering hook execution (same as TestFindMatchingTest)."""
          import importlib.util
          spec = importlib.util.spec_from_file_location("auto_test", HOOK)
          mod = importlib.util.module_from_spec(spec)
          spec.loader.exec_module(mod)
          return mod

      def test_no_tests_directory_returns_none(self, tmp_path, load_module):
          # No tests/ directory at all — rglob on non-existent path must not raise
          changed = tmp_path / "src" / "payments.py"
          result = load_module.find_matching_test(changed, "pytest", tmp_path)
          assert result is None

      def test_symlinked_test_file_found(self, tmp_path, load_module):
          # Create real test file and a symlink to it in the tests dir root
          tests_dir = tmp_path / "tests" / "unit"
          tests_dir.mkdir(parents=True)
          real_file = tests_dir / "test_payments.py"
          real_file.write_text("# test")
          # Symlink in tests root pointing to the real file
          link = tmp_path / "tests" / "test_payments_link.py"
          link.symlink_to(real_file)
          changed = tmp_path / "src" / "payments.py"
          result = load_module.find_matching_test(changed, "pytest", tmp_path)
          # rglob finds test_payments.py (real file) — symlink name doesn't match stem
          assert result == str(real_file)

      @pytest.mark.skipif(
          os.getuid() == 0,
          reason="root bypasses filesystem permissions — test not meaningful as root",
      )
      def test_permission_denied_on_tests_dir_returns_none(self, tmp_path, load_module):
          tests_dir = tmp_path / "tests"
          tests_dir.mkdir()
          tests_dir.chmod(0o000)
          try:
              changed = tmp_path / "src" / "payments.py"
              result = load_module.find_matching_test(changed, "pytest", tmp_path)
              assert result is None
          finally:
              # Restore permissions so pytest can clean up tmp_path
              tests_dir.chmod(0o755)

      def test_non_standard_extension_not_matched_for_pytest(self, tmp_path, load_module):
          # .ts file in tests/ — pytest runner only matches .py files
          tests_dir = tmp_path / "tests"
          tests_dir.mkdir()
          (tests_dir / "test_payments.ts").write_text("// ts test")
          changed = tmp_path / "src" / "payments.py"
          result = load_module.find_matching_test(changed, "pytest", tmp_path)
          assert result is None

      def test_vitest_missing_test_file_returns_none(self, tmp_path, load_module):
          # src/ exists but no .test.ts or .spec.ts for button
          src_dir = tmp_path / "src"
          src_dir.mkdir()
          changed = src_dir / "button.tsx"
          result = load_module.find_matching_test(changed, "vitest", tmp_path)
          assert result is None

      def test_empty_tests_directory_returns_none(self, tmp_path, load_module):
          # tests/ dir exists with no files inside
          (tmp_path / "tests").mkdir()
          changed = tmp_path / "src" / "payments.py"
          result = load_module.find_matching_test(changed, "pytest", tmp_path)
          assert result is None
  ```

  Run: `make test-unit` — must FAIL (class not yet in file)

- [ ] **Step 2: Implement (GREEN)**

  Adding the class above to `test_hooks_auto_test.py` IS the primary implementation step.

  If `test_no_tests_directory_returns_none` fails with an `OSError` (because `tests_dir.rglob(...)` raises when `tests_dir` does not exist), patch `hooks/auto-test.py`:

  ```python
  # hooks/auto-test.py — find_matching_test(), inside the "if runner == 'pytest':" block
  # BEFORE:
  for candidate in tests_dir.rglob(f"test_{stem}.py"):
      candidates.append(candidate)

  # AFTER:
  try:
      for candidate in tests_dir.rglob(f"test_{stem}.py"):
          candidates.append(candidate)
  except OSError:
      pass  # tests/ dir missing or not accessible — candidates stays as-is
  ```

  If `test_permission_denied_on_tests_dir_returns_none` also fails, the same `try/except OSError` patch covers it.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify `test_symlinked_test_file_found` assertion: `rglob` returns `test_payments.py` (the file whose name starts with `test_`), NOT `test_payments_link.py` (the symlink, which does not start with `test_payments` — it starts with `test_payments_link`). The stem of `payments.py` is `payments`, so the rglob pattern is `test_payments.py` — the link `test_payments_link.py` would NOT match. Update the test if needed so the symlink name matches the stem:

  ```python
  # Use a symlink that matches the expected pattern name:
  link = tmp_path / "tests" / "test_payments.py"  # same name as the real file
  # But we can't have two files with the same name — use a subdirectory:
  # Real file: tests/unit/test_payments.py
  # Symlink: tests/test_payments.py -> tests/unit/test_payments.py
  # rglob will find BOTH — first one found wins. Either path is acceptable.
  ```

  Adjust the assertion to accept either the real file or the symlink path if both match:

  ```python
  assert result in (str(real_file), str(link))
  ```

  Run: `make test-unit` — still PASS
