---
slug: zie-implement-agent-mode-warn
status: approved
date: 2026-04-04
---

# Design: /zie-implement Agent-Mode Warn-Only

## Problem

`commands/zie-implement.md` step 0 emits an interactive confirmation prompt when
not running in agent mode. This blocks execution waiting for a yes/cancel reply —
one unnecessary round-trip per common inline invocation.

## Solution

Replace the interactive prompt with a single warning line that prints and
immediately continues. No user input required.

## Acceptance Criteria

1. `commands/zie-implement.md` step 0 emits a warning line (no confirmation
   required) when not running in `--agent zie-framework:zie-implement-mode`.
2. Step 0 does **not** contain "yes", "cancel", "Continue anyway?", or any
   equivalent confirmation gate.
3. Execution continues immediately after the warning.
4. A test in `tests/unit/` asserts the old interactive prompt text is absent and
   the new warn-only text is present.
5. Existing tests in `tests/unit/test_commands_implement_resume.py` still pass.

## Scope

- **Changed:** `commands/zie-implement.md` — step 0 text only (markdown edit).
- **Changed:** new test file `tests/unit/test_command_zie_implement_agent_warn.py`.
- **No hook changes**, no Python logic changes.

## Non-Goals

- Removing the agent-mode check entirely.
- Adding auto-detection of agent mode via environment variables.
