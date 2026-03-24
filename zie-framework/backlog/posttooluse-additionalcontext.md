# Backlog: PostToolUse additionalContext — Test File Hints After Edits

**Problem:**
After every Write/Edit, Claude must manually figure out which test file covers
the changed code. This costs a Glob or Read tool call every TDD cycle. The
auto-test hook runs the test but doesn't tell Claude *which* test file was run.

**Motivation:**
PostToolUse supports `additionalContext` injection after any tool succeeds.
Injecting "affected test: tests/unit/test_hooks_X.py" after every file edit
saves Claude a lookup turn per TDD cycle — significant over 20+ cycles per
session.

**Rough scope:**
- Update `hooks/auto-test.py` (PostToolUse: Write|Edit) to also output
  `additionalContext` with the matched test file path (uses existing
  `find_matching_test()` logic)
- If no test file found: inject "No test file found for {filename} — write one"
- Keep auto-test debounce and execution behavior unchanged
- Add `hookSpecificOutput.additionalContext` to stdout JSON
- Tests: context injected correctly, None case, no regression on existing tests
