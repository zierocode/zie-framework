# Tests write directly to /tmp instead of pytest tmp_path

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`test_session_cleanup.py:30-31,45` and `test_hooks_wip_checkpoint.py:32-34`
write state files to real `/tmp/zie-*` paths. These paths persist across test
runs and can cross-contaminate: a failed test leaves state that changes the
outcome of the next test, or parallel test runs collide.

## Motivation

pytest's `tmp_path` fixture provides an isolated, auto-cleaned temporary
directory per test. Migration prevents flaky cross-test state bleed and makes
tests hermetic.
