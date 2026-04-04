# Spec: auto-test: Move additionalContext Injection After Debounce Check

status: draft

## Problem

`auto-test.py` emits the `additionalContext` JSON payload (lines 147–153) unconditionally,
before the debounce check (line 164). During rapid TDD edits within the debounce window, the
test run is suppressed — but the context injection still fires. Claude receives the same
test-file hint on every rapid-fire edit with zero new information, wasting context window
space and tokens on every turn.

In a typical RED/GREEN loop with 10 quick edits per minute, the debounce fires 8–9 times but
the context injection fires all 10. Moving the print inside the post-debounce path eliminates
all duplicate injections.

## Solution

Move the `print(json.dumps({"additionalContext": ...}))` call to after the debounce guard
exits — i.e., only emit when the hook has decided a test run will actually happen.

Concretely, in `hooks/auto-test.py`:

1. Delete the `additionalContext` block at lines 147–153 (before the debounce check).
2. Re-insert it after `safe_write_tmp(debounce_file, file_path)` at line 168, just before
   the test command is built.
3. Re-use `find_matching_test` for the `additionalContext` label (it is already called again
   at line 176 to build the pytest command — the second call is fine; the function is cheap).

No config key required. No new dependencies.

## Acceptance Criteria

- [ ] AC-1: When debounce suppresses a run, `additionalContext` is NOT emitted (stdout
      contains no `additionalContext` JSON key).
- [ ] AC-2: When a test run is NOT debounced, `additionalContext` IS emitted exactly once,
      before any test output.
- [ ] AC-3: The existing `TestAdditionalContextInjection` tests continue to pass with the
      moved print (non-debounced path is unchanged in behaviour).
- [ ] AC-4: `test_debounce_suppresses_rapid_second_call` is tightened to also assert
      `additionalContext` absent from stdout (documents the fix).
- [ ] AC-5: `make test-ci` passes with zero regressions.

## Out of Scope

- Changing the content or format of the `additionalContext` payload.
- Caching the `find_matching_test` result to avoid the second call (micro-optimisation,
  not needed).
- Any config toggle to restore the old behaviour.
