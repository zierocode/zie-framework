---
slug: lean-double-pretooluse-on-bash
date: 2026-04-04
approved: true
approved_at: 2026-04-04
model: sonnet
effort: low
---

# Plan: lean-double-pretooluse-on-bash

## Goal

Eliminate the per-Bash `safety_check_agent.py` overhead by removing it as a standalone PreToolUse hook entry. Inline its dispatch into `safety-check.py`. Mirror the ADR-043 consolidation pattern.

## Tasks

### Task 1 — Update `hooks/safety-check.py`

**File:** `hooks/safety-check.py`

In the Bash branch (after regex check), add inline dispatch:

```python
from hooks import safety_check_agent  # or relative import as appropriate

# After mode detection:
if mode in ("agent", "both"):
    try:
        result = safety_check_agent.evaluate(command, mode, config.get("safety_agent_timeout_s", 30))
        if result.blocked:
            print(result.message, file=sys.stderr)
            sys.exit(2)
    except Exception as e:
        print(f"[zie-framework] safety-check: agent import failed, falling back to regex: {e}", file=sys.stderr)
```

Remove any `if mode == "agent": sys.exit(0)` early-exit in the Bash branch (now handled internally).

### Task 2 — Update `hooks/hooks.json`

**File:** `hooks/hooks.json`

Remove the second PreToolUse entry that points to `safety_check_agent.py`. After this change only one PreToolUse hook fires for Bash events: `safety-check.py`.

Verify the remaining entry covers `Write|Edit|Bash` or `Bash` as appropriate.

### Task 3 — Update `hooks/safety_check_agent.py`

**File:** `hooks/safety_check_agent.py`

No logic changes. Verify `if __name__ == "__main__":` block is present and functional for standalone testing. Add a comment at the top:

```python
# This module is imported by safety-check.py for agent-mode dispatch.
# It is NOT registered as a standalone hook in hooks.json.
# Run directly only for manual testing: python3 safety_check_agent.py
```

### Task 4 — Update tests

**File:** `tests/test_safety_check.py`

Add integration cases:
- `mode="agent"` → agent evaluate is called (mock the function)
- `mode="both"` → regex runs first, then agent
- `mode="regex"` → agent evaluate is NOT called

**File:** `tests/test_safety_check_agent.py`

Verify direct import still works (mode dispatch via import).

### Task 5 — Run tests

```bash
make test-unit
```

All existing + new tests must pass.

## Acceptance Criteria

- `hooks.json` has only one PreToolUse entry for Bash events
- `safety-check.py` dispatches to `safety_check_agent.evaluate()` when mode is "agent" or "both"
- `safety_check_agent.py` is importable; `__main__` block intact for manual testing
- Import failure falls back to regex (no crash)
- Tests cover all three modes
