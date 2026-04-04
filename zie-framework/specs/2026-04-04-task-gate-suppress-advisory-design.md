# Design Spec: task-gate-suppress-advisory

**Slug:** task-gate-suppress-advisory
**Date:** 2026-04-04
**Status:** Approved

## Problem

`task-completed-gate.py:118` prints `"[zie-framework] task-completed-gate: advisory task — gate skipped"` to **stdout** when the task title doesn't match `implement` or `fix`. Claude Code injects hook stdout as context, so this string appears as noise on every non-implement `TaskCompleted` event (spec, plan, backlog, status, etc.).

## Decision

Remove the `print(...)` call at line 118. The hook should exit silently — consistent with how other hooks handle early exits (bare `sys.exit(0)`, no output).

Redirecting to stderr is not needed: this is not an error or a debug line. It is an informational no-op message that has no value.

## Acceptance Criteria

- AC1: A non-implement, non-fix task title causes the hook to exit 0 with **no stdout output**.
- AC2: Existing gate behavior (block on pytest failures, warn on uncommitted files) is unchanged for `implement`/`fix` titles.
- AC3: The test at `test_hooks_task_completed_gate.py:68` (`assert "advisory" in r.stdout.lower()`) is updated to assert `r.stdout == ""` (or equivalent empty check).
- AC4: `make test-fast` passes after the change.

## Scope

- **1-line removal** in `hooks/task-completed-gate.py` (line 118).
- **1-line test update** in `tests/unit/test_hooks_task_completed_gate.py` (line 68).

## Out of Scope

- Changing gate logic for implement/fix tasks.
- Adding a config flag to re-enable the message.
