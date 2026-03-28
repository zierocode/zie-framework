# audit: safety hook fix

## Problem

`safety-check.py` uses `sys.exit(1)` for all BLOCKS — but Claude Code PreToolUse
protocol requires `exit(2)` to actually block tool execution. `exit(1)` is a
non-blocking verbose-only error. Every block pattern (`rm -rf /`, `git push --force`,
`git reset --hard`, `--no-verify`) is currently silently ineffective.

Additional: hardcoded default URL `https://memory.zie-agent.cloud` in session-learn.py
and wip-checkpoint.py should not exist in source. Missing URL scheme validation.
Dead WARNS entry for `--force-with-lease` is shadowed by BLOCKS.

## Motivation

The safety hook is the primary user-visible safety guardrail of zie-framework.
If it doesn't actually block anything, the entire feature is a false sense of security.
Fix is XS effort but impact is Critical.

## Scope

- `hooks/safety-check.py` — change `sys.exit(1)` → `sys.exit(2)` on all BLOCKS
- `hooks/safety-check.py` — remove dead WARNS entry for `--force-with-lease`
- `hooks/session-learn.py` + `hooks/wip-checkpoint.py` — remove hardcoded default URL,
  add `assert api_url.startswith("https://")` before HTTP call
- `tests/unit/test_hooks_safety_check.py` — update all block assertions from
  `r.returncode == 1` to `r.returncode == 2`
- Add prevention: test explicitly asserts exit code is 2, not just non-zero
- `hooks/safety-check.py` — harden `rm -rf` pattern to also match `rm -rf ./`
  (trailing slash variant, finding #13)

## Prevention mechanism

Test suite will assert `r.returncode == 2` (not just `!= 0`) for every block pattern.
Any future edit that changes exit code regresses the test immediately.
