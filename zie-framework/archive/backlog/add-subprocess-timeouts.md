# Add Subprocess Timeouts to All Hooks

**Source**: audit-2026-03-24b H3-quality (Agent C)
**Effort**: S
**Score impact**: +8 (High eliminated → Quality +8)

## Problem

5 hooks call `subprocess.run()` for git commands without `timeout=` parameter.
If git hangs (lock file, network mount, large repo), the hook blocks the entire
Claude session indefinitely.

Affected hooks (failure-context.py already correct with timeout=5):
- `hooks/auto-test.py:138` — pytest subprocess
- `hooks/safety_check_agent.py:80` — claude CLI subprocess (has 30s, needs audit)
- `hooks/sdlc-compact.py:54` — git branch
- `hooks/sdlc-compact.py:66` — git log
- `hooks/stop-guard.py:53` — git status
- `hooks/task-completed-gate.py:61` — git status

## Motivation

`failure-context.py` already uses `timeout=5` as the correct pattern. One hook
getting this right means the fix is known — just needs to be applied uniformly.

## Scope

- Add `timeout=5` to all subprocess.run() git calls
- Wrap `subprocess.TimeoutExpired` identically to failure-context.py pattern
- For `auto-test.py`: use the configurable `auto_test_timeout_ms` from .config
  (already read, just pass to subprocess)
- For `safety_check_agent.py`: existing 30s timeout is fine; verify it's enforced

## Acceptance Criteria

- [ ] All subprocess.run() calls have explicit timeout parameter
- [ ] SubprocessTimeoutExpired caught and hook exits 0 with warning
- [ ] auto-test.py uses auto_test_timeout_ms config value
- [ ] At least 1 timeout test per hook (can reuse git-not-found pattern)
