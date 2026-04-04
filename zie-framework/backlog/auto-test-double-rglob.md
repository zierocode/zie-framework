# auto-test: Cache find_matching_test Result — Avoid Double rglob Per Edit

## Problem

`auto-test.py` calls `find_matching_test(changed, test_runner, cwd)` twice per non-debounced edit: once at line 148 (to build the `additionalContext` message) and again at line 176 (to build the test command). Both calls perform an identical `tests_dir.rglob(f"test_{stem}.py")` filesystem scan. The second call is redundant — the first result is discarded.

## Motivation

Two full recursive filesystem scans per code edit in a TDD session. On large test suites or slow filesystems this adds measurable latency to every edit cycle. Simple fix: cache the result in a local variable between both uses.

## Rough Scope

- Call `find_matching_test` once, store result in a variable
- Use cached result for both `additionalContext` construction and test command building
- One-line fix in `auto-test.py`; update any tests that mock `find_matching_test`
