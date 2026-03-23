# audit: test hardening

## Problem

Tests use shared mutable /tmp state without cleanup fixtures, causing non-deterministic
ordering failures. Key behaviors have no tests or weak assertions:

- `intent-detect.py` output validated by substring check, not JSON parse
- `find_matching_test()` function has zero dedicated unit tests
- Frontmatter/long-message suppression guards untested
- ROADMAP edge cases (missing, empty, malformed) not covered
- Debounce window logic not tested with varied `auto_test_debounce_ms`
- /tmp cleanup inconsistent across test files

## Motivation

Tests that pass on a clean machine but fail on a developer's machine (due to stale /tmp)
are worse than no tests — they create false confidence and alert fatigue.
The JSON output validation gap means intent-detect could silently break its Claude Code
protocol contract without any test failing.

## Scope

- Add `@pytest.fixture(autouse=True)` teardowns for `/tmp/zie-*` files in affected
  test classes (test_hooks_auto_test.py, test_hooks_wip_checkpoint.py)
- Strengthen intent-detect assertions: `json.loads(r.stdout)["additionalContext"]`
  instead of substring check
- Add tests for frontmatter skip (`message.startswith("---")`) and
  long message skip (`len(message) > 500`)
- Add direct unit tests for `find_matching_test()` — import function, no subprocess
- Add ROADMAP edge case tests for wip-checkpoint and session-learn
  (missing ROADMAP, empty Now, malformed items)
- Add debounce tests: `debounce_ms=0` (always run), `debounce_ms=999999` (always skip)
- Standardize /tmp cleanup pattern across all hook test files

## Prevention mechanism

`autouse=True` fixtures enforce cleanup structurally — any new test class inherits
teardown automatically. JSON parse assertion means any hook output format regression
fails the test.
