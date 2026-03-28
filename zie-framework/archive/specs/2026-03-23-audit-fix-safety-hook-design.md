---
slug: audit-fix-safety-hook
approved: true
approved_at: 2026-03-23
backlog: backlog/audit-fix-safety-hook.md
---

# Spec: Safety Hook Fix

## Problem

`safety-check.py` calls `sys.exit(1)` on all BLOCK matches, but the Claude Code
PreToolUse protocol requires `exit(2)` to actually block tool execution — `exit(1)`
is a non-blocking verbose-only signal, making every safety guard silently ineffective.
Additionally, two hooks (`session-learn.py`, `wip-checkpoint.py`) contain a hardcoded
fallback URL in source with no scheme validation, and the `rm -rf ./` trailing-slash
variant is not caught by the current filesystem destruction pattern.

## Approach

Direct surgical fixes across three files — no refactor, no new abstractions. The
exit-code bug is a one-liner change; the dead WARNS entry and hardcoded URL are
deletions; the `rm -rf ./` gap is a regex extension; and the test suite is updated to
assert the exact exit code `2` so any future regression fails immediately.

## Acceptance Criteria

- [ ] AC-1: `safety-check.py` calls `sys.exit(2)` (not `sys.exit(1)`) on every BLOCKS
  match, causing Claude Code to actually block the tool call.
- [ ] AC-2: The dead WARNS entry for `--force-with-lease` is removed from `safety-check.py`
  (it is already caught by the `--force\b` BLOCKS pattern and never reaches WARNS).
- [ ] AC-3: The `rm -rf` BLOCKS pattern in `safety-check.py` matches the trailing-slash
  variant `rm -rf ./` in addition to existing dot variants.
- [ ] AC-4: The hardcoded default URL `"https://memory.zie-agent.cloud"` is removed from
  `session-learn.py` and `wip-checkpoint.py`; when `ZIE_MEMORY_API_URL` is not set,
  both hooks exit cleanly without making any HTTP call.
- [ ] AC-5: Both `session-learn.py` and `wip-checkpoint.py` validate that `api_url`
  starts with `"https://"` before any HTTP call is attempted; an invalid or missing URL
  causes a clean exit, not a crash.
- [ ] AC-6: All block-case assertions in `test_hooks_safety_check.py` assert
  `r.returncode == 2` (not `r.returncode == 1`), making the exit-code contract explicit
  and regression-proof.
- [ ] AC-7: The existing `test_force_with_lease_is_blocked` test (which verifies
  `--force-with-lease` hits the BLOCKS path) continues to pass after the dead WARNS
  entry is removed, and still asserts `returncode == 2`.
- [ ] AC-8: Pass-through and warn-case tests (`returncode == 0`) are unaffected — the
  full test suite passes with `make test-unit`.

## Out of Scope

- No changes to any other hook files beyond `safety-check.py`, `session-learn.py`,
  and `wip-checkpoint.py`.
- No new BLOCKS or WARNS patterns beyond the `rm -rf ./` trailing-slash fix.
- No changes to the Claude Code plugin manifest or hooks.json configuration.

## Files Changed

- `hooks/safety-check.py` — exit code `1` → `2`; remove dead `--force-with-lease`
  WARNS entry; extend `rm -rf` pattern to cover `./` trailing-slash variant.
- `hooks/session-learn.py` — remove hardcoded default URL; add `https://` scheme
  validation guard before HTTP call.
- `hooks/wip-checkpoint.py` — remove hardcoded default URL; add `https://` scheme
  validation guard before HTTP call.
- `tests/unit/test_hooks_safety_check.py` — update all block-case `returncode == 1`
  assertions to `returncode == 2`.
