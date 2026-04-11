# Backlog: Fix verify skill check 2 to reuse test_output (no re-run)

**Problem:**
verify/SKILL.md check 1 correctly guards: "if test_output provided and non-empty,
skip re-running make test-unit." But check 2 ("no regressions") says "Run the full
suite" without an equivalent guard. In tests-only scope, check 1 uses test_output
but check 2 may trigger a second full test run even when test_output was provided
by the caller.

**Motivation:**
Running the full test suite twice per verify invocation is pure wall-clock waste
(2+ minutes of CI time). The fix is a one-line guard in check 2 matching the
existing pattern from check 1.

**Rough scope:**
- Add same `test_output` guard to check 2: "if test_output provided → use it,
  don't re-run make test-unit"
- Make the pattern consistent across all checks in verify SKILL.md
- Tests: verify with test_output provided → make test-unit called exactly once (or zero)
