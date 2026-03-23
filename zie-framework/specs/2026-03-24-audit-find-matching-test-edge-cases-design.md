---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-find-matching-test-edge-cases.md
---

# find_matching_test() — Edge Case Tests for Missing/Unusual Test Directory Structures — Design Spec

**Problem:** `find_matching_test()` in `hooks/auto-test.py` has no tests for: missing `tests/` directory entirely, symlinked test files, permission-denied on test files, and non-standard test file extensions — all realistic CI or first-use conditions.

**Approach:** Add a new test class `TestFindMatchingTestEdgeCases` to `test_hooks_auto_test.py`, using the existing `load_module` fixture pattern from `TestFindMatchingTest` to import `find_matching_test` directly. Tests use `tmp_path` to create controlled filesystem states. No changes to `hooks/auto-test.py` are expected unless a test reveals an unhandled exception.

**Components:**
- `tests/unit/test_hooks_auto_test.py` — new class `TestFindMatchingTestEdgeCases`
- `hooks/auto-test.py` — `find_matching_test()` lines 14-43 (may require defensive handling if `tests/` absence raises)

**Data Flow — test cases to add:**

1. `test_no_tests_directory_returns_none`:
   - `tmp_path` has no `tests/` subdirectory at all.
   - Call `find_matching_test(tmp_path / "src" / "payments.py", "pytest", tmp_path)`.
   - Assert result is `None` (not an exception).
   - Rationale: `tests_dir.rglob(...)` on a non-existent directory raises `OSError` in some Python versions — current code does not guard this.

2. `test_symlinked_test_file_found`:
   - Create `tests/unit/test_payments.py` as a real file.
   - Create `tests/test_payments_link.py` as a symlink pointing to the real file.
   - Call with `changed = tmp_path / "src" / "payments.py"`.
   - Assert result is the real file path (symlink is followed by `Path.exists()`).

3. `test_permission_denied_on_tests_dir_returns_none`:
   - Create `tests/` directory and `chmod 000` it.
   - Call `find_matching_test(...)`.
   - Assert result is `None` (no crash).
   - Skip on platforms where chmod 000 is not effective (e.g. running as root): use `pytest.mark.skipif(os.getuid() == 0, reason="root bypasses permissions")`.
   - Restore permissions in teardown (`chmod 755`) to allow `tmp_path` cleanup.

4. `test_non_standard_extension_not_matched_for_pytest`:
   - Create `tests/test_payments.ts` (TypeScript file in a pytest project).
   - Call with runner `"pytest"` and `changed = tmp_path / "src" / "payments.py"`.
   - Assert result is `None` — pytest runner only looks for `.py` files.

5. `test_vitest_missing_test_file_returns_none`:
   - `tmp_path` has `src/` directory but no `button.test.ts` or `button.spec.ts`.
   - Call with runner `"vitest"` and `changed = tmp_path / "src" / "button.tsx"`.
   - Assert result is `None`.

6. `test_empty_tests_directory_returns_none`:
   - Create `tests/` directory with no files inside.
   - Call with runner `"pytest"` and any changed path.
   - Assert result is `None`.

**Edge Cases:**
- `Path.rglob()` on a non-existent path raises `OSError` (not `FileNotFoundError`) in CPython 3.12+ — the fix in `auto-test.py` should wrap the `rglob` call in a `try/except OSError` returning `None`. Test #1 will expose this if it is not already guarded.
- Symlinks that point to non-existent targets: `c.exists()` returns `False` for broken symlinks — no special handling needed, test #2 uses a valid symlink.
- The `chmod 000` test (#3) requires cleanup in `finally` or a fixture to avoid leaving `tmp_path` unremovable by pytest's cleanup.
- `find_matching_test` is called from the `__main__` block only when executed as a hook — but the `load_module` fixture imports the module without running `__main__`, so `find_matching_test` can be called directly in all tests.

**Out of Scope:**
- Testing `find_matching_test` with runner `"jest"` — it uses the same candidate-list pattern as `"vitest"` and is already implicitly covered.
- Testing the full hook subprocess flow for these edge cases (covered by the guardrail tests in `TestAutoTestGuardrails`).
- Adding support for non-standard extensions to `find_matching_test` (separate feature request).
