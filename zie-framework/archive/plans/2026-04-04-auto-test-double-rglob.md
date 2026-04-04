# Plan: Cache find_matching_test Result in auto-test.py

status: approved

## Tasks

- [ ] RED: Add a test to `tests/unit/test_hooks_auto_test.py` in a new class
  `TestFindMatchingTestCalledOnce` that patches `find_matching_test` via
  `unittest.mock.patch` (target `auto_test.find_matching_test`) and asserts
  `call_count == 1` after running a full non-debounced Edit event for a pytest
  project with a matching test file. Confirm it fails (call_count is 2).

- [ ] GREEN: In `hooks/auto-test.py`, remove the second call to
  `find_matching_test` at line 176 and replace the `matching_test` local
  variable assignment with a reference to `_ctx_test` (the variable already
  holding the result from the first call at line 148). Confirm the new test
  passes and all existing tests pass.

- [ ] REFACTOR: Rename `_ctx_test` → `matching_test` throughout the block
  (lines 148–153 and the command-builder at ~176) so both usages share the same
  clearly named variable. Run `make lint` and `make test-fast` to verify.

## Files to Change

- `hooks/auto-test.py` — remove second `find_matching_test` call; unify
  variable name
- `tests/unit/test_hooks_auto_test.py` — add `TestFindMatchingTestCalledOnce`
  class with mock-based call-count assertion

## Notes

- The mock must patch `find_matching_test` in the `__main__` execution path.
  Since the test suite imports the module via `importlib`, prefer patching via
  subprocess + a side-channel, or restructure the test to use the `load_module`
  fixture and call the `__main__` block indirectly. Simplest approach: run the
  hook subprocess with a custom `tests_dir` and count filesystem calls via a
  temp directory with a counter file, or patch using
  `unittest.mock.patch.object` on the loaded module before triggering the main
  block. Confirm approach during RED step.
- If `auto-test-context-debounce` is implemented in the same sprint, coordinate
  the variable placement: move the single `find_matching_test` call to after the
  debounce check alongside the `additionalContext` print.
