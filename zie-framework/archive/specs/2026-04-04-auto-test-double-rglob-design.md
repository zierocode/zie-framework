# Spec: Cache find_matching_test Result in auto-test.py

status: draft

## Problem

`auto-test.py` calls `find_matching_test(changed, test_runner, cwd)` twice per
non-debounced edit event:

1. **Line 148** — result stored in `_ctx_test`, used to build the
   `additionalContext` message printed before the debounce check.
2. **Line 176** — result stored in `matching_test`, used to build the pytest
   command after the debounce check.

Both calls execute an identical `tests_dir.rglob(f"test_{stem}.py")` recursive
filesystem scan. The first result is discarded; the second repeats the same I/O
from scratch. On large test suites or slow/networked filesystems this doubles
the filesystem work on every TDD edit cycle.

## Solution

Call `find_matching_test` once, store the result in a local variable, and
reference that variable in both places.

Concretely, replace the two independent calls with a single call just before
the `additionalContext` block (where the first call currently lives), then
replace the `find_matching_test(changed, "pytest", cwd)` call at line 176 with
the cached variable.

### Coordination with `auto-test-context-debounce`

The `auto-test-context-debounce` backlog item moves the `additionalContext`
print to after the debounce check. If both items are implemented together:

- The single `find_matching_test` call should move to after the debounce check
  as well (since it feeds the context injection that moves there).
- The cached variable is then available for both the context injection and the
  command builder — no additional change needed.

If implemented independently (this item first), place the single call where the
first call currently lives (before the debounce check) and replace only the
second call with the cached result.

## Acceptance Criteria

1. `find_matching_test` is called exactly once per non-debounced edit in the
   pytest code path.
2. The `additionalContext` message continues to display the correct test file
   (or "no test file" hint) — behaviour is unchanged.
3. The test command continues to target the correct test file when one exists.
4. All existing tests in `tests/unit/test_hooks_auto_test.py` pass without
   modification (no externally visible behaviour change).
5. A new unit test asserts that `find_matching_test` is called at most once when
   a matching test file exists and debounce is inactive.

## Out of Scope

- Moving the `additionalContext` injection relative to the debounce check
  (tracked separately in `auto-test-context-debounce`).
- Caching across multiple hook invocations / sessions.
- Changes to the vitest/jest code paths (they do not call `find_matching_test`
  in the command-builder block).
