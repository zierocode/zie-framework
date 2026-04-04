---
slug: zie-implement-agent-mode-warn
spec: zie-framework/specs/2026-04-04-zie-implement-agent-mode-warn-design.md
approved: true
date: 2026-04-04
---

# Plan: /zie-implement Agent-Mode Warn-Only

## Overview

Single-step change: replace the interactive confirm/cancel prompt in step 0 of
`commands/zie-implement.md` with a non-blocking warning line. Add a test to
assert the new behavior.

---

### Task 1 — Edit zie-implement.md step 0

**File:** `commands/zie-implement.md`

Replace lines 17–19 (step 0):

```
0. **Pre-flight: Agent mode check** — if not running with `--agent zie-framework:zie-implement-mode`:
   display `⚠️ Running /zie-implement outside agent session. Recommended: claude --agent zie-framework:zie-implement-mode. Continue anyway? (yes / cancel)`
   yes → continue, cancel → stop.
```

With:

```
0. **Pre-flight: Agent mode check** — if not running with `--agent zie-framework:zie-implement-mode`:
   print `⚠️ Running /zie-implement outside agent session. For best results use: claude --agent zie-framework:zie-implement-mode` and continue immediately.
```

**AC check:** step 0 text contains no "yes", "cancel", or "Continue anyway?".

---

### Task 2 — Add test

**File:** `tests/unit/test_command_zie_implement_agent_warn.py`

```python
"""Structural tests: /zie-implement step 0 must warn-only, not block."""
import os
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMPLEMENT_CMD = Path(REPO_ROOT) / "commands" / "zie-implement.md"


class TestAgentModeWarnOnly:
    def _src(self):
        return IMPLEMENT_CMD.read_text()

    def test_no_interactive_confirmation(self):
        """Step 0 must not ask for yes/cancel confirmation."""
        src = self._src()
        assert "Continue anyway?" not in src, (
            "zie-implement.md step 0 must not contain interactive confirmation"
        )
        assert "yes / cancel" not in src, (
            "zie-implement.md step 0 must not contain yes/cancel gate"
        )

    def test_warn_only_present(self):
        """Step 0 must emit a warning and continue immediately."""
        src = self._src()
        assert "continue immediately" in src or "continue" in src.lower(), (
            "zie-implement.md step 0 must document warn-and-continue behavior"
        )
        assert "zie-implement-mode" in src, (
            "zie-implement.md step 0 must mention the recommended agent mode"
        )
```

---

## Verification

```bash
make lint
make test-fast
```

Both must pass with zero failures.
