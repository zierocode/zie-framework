---
date: 2026-04-15
status: approved
slug: audit-error-path-coverage
---

# Design Spec: audit-error-path-coverage

## Problem

35 hook modules contain `except` blocks with no test coverage verifying fallback behavior. The audit found 34% of these silently swallow errors. The companion `audit-error-handling-cleanup` plan adds stderr logging, but without error-path tests, any future refactoring risks breaking silent fallback paths with no regression safety net.

## Solution

Add `@pytest.mark.error_path` tests for the 15 in-scope hooks listed in `check_error_path_coverage.py`. Each test exercises a specific exception path by monkeypatching or removing dependencies, then asserts the hook exits 0 (ADR-003) and degrades gracefully (stderr log or no crash). Priority order: stop-handler, session-resume, intent-sdlc, utils_roadmap, auto-test, then the remaining 10.

## Rough Scope

- One test file per hook (or additions to existing files where tests already exist): `tests/unit/test_*_error_paths.py`
- Tests import hook functions and call them with monkeypatched deps that raise exceptions
- Each test validates: exit 0, no stdout corruption, optional stderr logging
- Update `check_error_path_coverage.py` if hook names change

## Files Changed

- `tests/unit/test_stop_handler_error_paths.py` (new)
- `tests/unit/test_session_resume_error_paths.py` (new)
- `tests/unit/test_intent_sdlc_error_paths.py` (new)
- `tests/unit/test_utils_roadmap_error_paths.py` (new)
- `tests/unit/test_auto_test_error_paths.py` (new)
- Existing test files for remaining 10 hooks (additions)