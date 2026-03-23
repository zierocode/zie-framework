# find_matching_test() edge cases not covered in tests

**Severity**: Low | **Source**: audit-2026-03-24

## Problem

`hooks/auto-test.py:14-43` and its test coverage in `test_hooks_auto_test.py`
don't exercise: missing `tests/` directory entirely, symlinked test files,
permission-denied on test files, or non-standard test file extensions. These are
realistic CI/environment conditions.

## Motivation

Ensures auto-test degrades gracefully rather than crashing when the test
directory structure is unusual. Especially important for first-time projects that
haven't created tests/ yet.
