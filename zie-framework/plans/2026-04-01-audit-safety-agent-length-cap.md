---
slug: audit-safety-agent-length-cap
status: approved
approved: true
date: 2026-04-01
---

# Plan: Add Command Length Cap to safety_check_agent.py

## Overview

Add a 4096-character cap in `invoke_subagent()` before constructing the prompt.
Commands longer than 4096 chars are truncated with a visible `[... truncated]`
marker. Prevents unexpectedly large prompts in `"agent"` mode.

**Spec:** `zie-framework/specs/2026-04-01-audit-safety-agent-length-cap-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | `invoke_subagent` called with a command > 4096 chars → prompt contains `[... truncated]` |
| AC-2 | `invoke_subagent` called with a command ≤ 4096 chars → prompt uses full command, no truncation marker |
| AC-3 | Module-level constant `MAX_CMD_CHARS = 4096` defined |
| AC-4 | All tests pass; `make test-ci` exits 0 |

---

## Tasks

### Task 1 — Write failing tests (RED)

**File:** `tests/unit/test_safety_check_agent.py`

Add `TestCommandLengthCap` class:

```python
from unittest.mock import patch, MagicMock
from hooks.safety_check_agent import invoke_subagent, MAX_CMD_CHARS


class TestCommandLengthCap:
    def test_long_command_prompt_contains_truncation_marker(self):
        """AC-1."""
        long_cmd = "x" * (MAX_CMD_CHARS + 100)
        captured_prompts = []

        def mock_run(args, **kwargs):
            # args = ["claude", "--print", prompt]
            captured_prompts.append(args[2])
            m = MagicMock()
            m.stdout = "ALLOW"
            return m

        with patch("subprocess.run", side_effect=mock_run):
            invoke_subagent(long_cmd)

        assert captured_prompts, "subprocess.run was not called"
        assert "[... truncated]" in captured_prompts[0]

    def test_short_command_not_truncated(self):
        """AC-2."""
        short_cmd = "ls -la"
        captured_prompts = []

        def mock_run(args, **kwargs):
            captured_prompts.append(args[2])
            m = MagicMock()
            m.stdout = "ALLOW"
            return m

        with patch("subprocess.run", side_effect=mock_run):
            invoke_subagent(short_cmd)

        assert captured_prompts
        assert "[... truncated]" not in captured_prompts[0]
        assert short_cmd in captured_prompts[0]

    def test_max_cmd_chars_constant_is_4096(self):
        """AC-3."""
        assert MAX_CMD_CHARS == 4096
```

Run `make test-unit` — RED confirmed (3 failures — MAX_CMD_CHARS not defined,
truncation not implemented).

---

### Task 2 — Implement (GREEN)

**File:** `hooks/safety_check_agent.py`

**Add constant after imports:**
```python
MAX_CMD_CHARS = 4096
```

**Update `invoke_subagent` — add truncation before prompt construction (before line 48):**

Before:
```python
def invoke_subagent(command: str, timeout: int = 30) -> str:
    """Call claude CLI to evaluate the command. Returns agent response text."""
    prompt = (
```

After:
```python
def invoke_subagent(command: str, timeout: int = 30) -> str:
    """Call claude CLI to evaluate the command. Returns agent response text."""
    if len(command) > MAX_CMD_CHARS:
        command = command[:MAX_CMD_CHARS] + "\n[... truncated]"
    prompt = (
```

Run `make test-unit` — GREEN.

---

### Task 3 — Full suite gate

Run `make test-ci` — must exit 0.

---

## Test Strategy

| Layer | Test | AC |
|-------|------|----|
| Unit | test_long_command_prompt_contains_truncation_marker | AC-1 |
| Unit | test_short_command_not_truncated | AC-2 |
| Unit | test_max_cmd_chars_constant_is_4096 | AC-3 |

---

## Rollout

1. Write failing tests (Task 1) — RED.
2. Add constant + truncation (Task 2) — GREEN.
3. Run `make test-ci` (Task 3) — no regression.
4. Mark ROADMAP Done.
