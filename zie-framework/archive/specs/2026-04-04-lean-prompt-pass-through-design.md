---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-prompt-pass-through.md
---

# Lean Prompt Pass-Through — Design Spec

**Problem:** `intent-sdlc.py` fires on every UserPromptSubmit and injects SDLC state into
context even when the message is a slash command (e.g. `/sprint slug1 slug2 --dry-run`),
which already carries its own full context via SKILL.md. The existing early-exit guard
(`len(first_token) < 20`) does not catch slash commands with arguments.

**Approach:** Move the slash-command early-exit check into the outer guard block
(before `get_cwd()` and any filesystem I/O), changing the condition from
`len(first_token) < 20` to `first_token.startswith("/")`. The outer guard is the
correct tier for this check per the hook two-tier pattern (ADR-003): it is a pure
in-memory check on the prompt string with zero I/O, and any message starting with `/`
should unconditionally skip injection regardless of cwd or ROADMAP state.

**Components:**
- `hooks/intent-sdlc.py` — sole change; outer guard block (lines 222–241), replace
  the existing `startswith("/") and len < 20` condition with `startswith("/")`

**Data Flow:**
1. UserPromptSubmit event arrives
2. Outer guard reads `event["prompt"]`, strips and lowercases it
3. `message.startswith("/")` → `sys.exit(0)` immediately (no cwd check, no roadmap read)
4. All other messages proceed to inner operations unchanged

**Edge Cases:**
- `/sprint slug1 slug2 --dry-run` — starts with `/`, exits immediately (fixed)
- `/status` — already caught by old guard (len=7 < 20), still caught by new guard
- `/implement` — len=10 < 20, still caught
- `/ ` or `/` alone — starts with `/`, exits (acceptable; degenerate input)
- Message like `"i want to /spec something"` — does NOT start with `/`, passes through normally (correct)
- Empty message, message < 3 chars — caught by earlier guard, never reaches slash check

**Out of Scope:**
- Changing intent detection logic or SDLC state injection content
- Suppressing injection for non-slash-command short messages
- Handling messages that contain `/` mid-string
- Any changes to other hooks
