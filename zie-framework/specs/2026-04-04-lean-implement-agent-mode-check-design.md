---
approved: true
approved_at: 2026-04-04
---

# Lean implement Agent-Mode Check — Design Spec

**Problem:** `commands/implement.md` Step 0 prints a multi-line warning and blocks on a yes/no confirmation when the session is not running inside `--agent zie-framework:zie-implement-mode`. Every normal inline invocation hits this interactive gate, adding an unnecessary round-trip and ~100–200 tokens of preamble before any real work begins.

**Approach:** Remove the yes/no gate and `if no → STOP` branch entirely. Replace Step 0 with a single non-blocking advisory tip. Execution continues immediately — no user input required. An existing test file (`test_command_zie_implement_agent_warn.py`) currently asserts the blocking behavior; those assertions must be inverted to assert the advisory-only pattern.

**Exact advisory tip text (Step 0 replacement):**

```
Tip: for best results run inside `claude --agent zie-framework:zie-implement-mode`
```

This matches the framework's advisory tone (lightweight, non-blocking, no emoji — consistent with `retro.md` "Advisory only" pattern). The `Recommended:` prefix from the old Step 0 is dropped because it implies a required action; `Tip:` is softer and appropriate for an informational-only message.

**Components:**
- `commands/implement.md` — Step 0 text edit (markdown only, no Python changes)
- `tests/unit/test_command_zie_implement_agent_warn.py` — invert assertions: remove `test_interactive_confirmation_present` and `test_stop_on_no`; add structural assertion that Step 0 does NOT contain blocking prompt text and DOES contain the advisory tip

**Data Flow:**
1. User invokes `/implement` in any session
2. `implement.md` Step 0 executes
3. Advisory tip prints inline (one line)
4. Execution continues to Step 1 (zie-framework/ existence check) with zero round-trips

**Edge Cases:**
- Session IS running inside `--agent zie-framework:zie-implement-mode` — tip still prints (harmless; no detection logic added; YAGNI)
- Existing tests asserting old blocking text — must be replaced or inverted to avoid false-pass after the change
- Other commands that reference Step 0 language (none identified; no downstream impact)

**Out of Scope:**
- Auto-detecting agent mode via environment variable or process inspection
- Making the tip conditional (print only when NOT in agent mode)
- Adding a `.config` knob to control tip visibility
- Changes to any hook, Python file, or other command
