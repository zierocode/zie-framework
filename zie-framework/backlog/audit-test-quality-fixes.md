---
tags: [debt]
---

# Fix Test Quality Issues (Dead Refs, Misplaced Files, Flakiness)

## Problem

- test_stop_guard.py references non-existent `hooks/stop-guard.py` (renamed to stop-handler)
- 9 test files in `tests/` root instead of `tests/unit/` or `tests/integration/`
- `time.sleep()` in 3 test files creates timing-dependent flakiness
- TestLookupCache class in production hook triggers PytestCollectionWarning
- test_test_fast_acceptance.py in `tests/unit/` but marked `@pytest.mark.integration`

## Motivation

Dead test references mask real failures. Misplaced tests bypass correct test organization. Time-dependent tests cause CI flakiness.

## Rough Scope

- Rename/update test_stop_guard.py → test_stop_handler.py
- Move 9 root-level test files to tests/unit/ with appropriate markers
- Replace time.sleep() with mock/patch-based TTL testing
- Add `__test__ = False` to TestLookupCache class in auto-test.py
- Move test_test_fast_acceptance.py to tests/integration/