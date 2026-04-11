---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-notification-log-double-guard.md
---

# lean-notification-log-double-guard — Design Spec

**Problem:** `notification-log.py` checks `notification_type == "permission_prompt"` twice — once as an outer guard (line 20–21) and again as an inner condition (line 68) — even though `hooks.json` already filters the hook to `permission_prompt` events via the `matcher` field, making both in-code checks redundant.

**Approach:** Remove the inner `if notification_type == "permission_prompt":` condition and de-indent the block beneath it. Add a one-line comment above the de-indented block explaining that the `hooks.json` matcher guarantees only `permission_prompt` events reach this point. The outer guard (lines 17–23) is retained as defensive first-line parsing; the inner check is pure dead code.

**Components:**
- `hooks/notification-log.py` — remove inner type guard; de-indent block; add explanatory comment

**Data Flow:**
1. Claude Code fires a `Notification` event
2. `hooks.json` matcher `"permission_prompt"` filters — only matching events invoke the hook
3. Outer guard (try/except block, lines 17–23) parses the event and exits 0 on any parse failure; the `notification_type != "permission_prompt"` early-exit remains as a defensive fallback
4. Inner operations block (lines 64–82) now runs unconditionally — no inner type check needed
5. `_append_and_write` logs the permission message; count-threshold check emits `additionalContext` when ≥ 3 repeats are detected

**Edge Cases:**
- If Claude Code ever removes or ignores the matcher, the outer guard still handles non-`permission_prompt` events correctly — no regression
- De-indenting the block removes one level of nesting; no logic paths change
- Existing tests that mock the event payload continue to pass without modification since the observable behaviour is identical

**Out of Scope:**
- Changing or removing the outer guard — it remains as defensive parse protection per ADR-003
- Handling `idle_prompt` notification type (mentioned in the module docstring but not currently implemented)
- Any changes to test files beyond confirming they still pass
