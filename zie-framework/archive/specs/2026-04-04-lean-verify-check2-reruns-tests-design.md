---
slug: lean-verify-check2-reruns-tests
status: draft
created: 2026-04-04
---

# Design: Lean Verify — Check 2 Skips Redundant test-unit Run

## Problem

`skills/verify/SKILL.md` check 2 ("ไม่มี regressions") unconditionally tells
the model to "run the full suite." When a caller already provides `test_output`
(e.g. from `make test-unit` run during check 1), check 2 triggers a second
`make test-unit` invocation — redundant I/O with no new information.

Check 1 already has a `test_output` guard: if `test_output` is provided and
non-empty, it reuses that result instead of re-running. Check 2 has no such
guard, so the redundant run happens on every verify call that supplies
`test_output`.

## Solution

Add the same `test_output` guard to check 2:

- If `test_output` was provided and non-empty → reuse it for the regression
  check (compare pass count to previous run using the already-available
  output). Do not run `make test-unit` again.
- If `test_output` is absent or empty → run `make test-unit` as today.

This mirrors the existing check 1 pattern exactly and requires only a wording
change inside the check 2 section of `skills/verify/SKILL.md`.

## Components

- `skills/verify/SKILL.md` — check 2 section updated with `test_output` guard.

## Acceptance Criteria

- Check 2 in `skills/verify/SKILL.md` explicitly states: if `test_output` is
  provided and non-empty, reuse it for the regression check instead of running
  `make test-unit`.
- When `test_output` is absent or empty, check 2 still runs `make test-unit`
  (backward compatible).
- No other check behavior is changed.
- All existing tests pass.
