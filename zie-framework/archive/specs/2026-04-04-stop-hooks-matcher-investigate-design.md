---
approved: true
approved_at: 2026-04-04
backlog: backlog/stop-hooks-matcher-investigate.md
---

# Stop Hook Matcher Support Investigation — Design Spec

**Problem:** All 4 Stop hooks (`stop-guard.py`, `compact-hint.py`, `session-learn.py`, `session-cleanup.py`) fire on every session stop with no matcher. The `hooks.json` comment block does not document whether Stop supports matchers, leaving the question open for future maintainers.

**Investigation Result:** Stop events **do not support matchers**. Per Anthropic's Claude Code hooks reference, the matcher field is only meaningful for tool-based events (PreToolUse, PostToolUse, PostToolUseFailure) and pattern-keyed events (SubagentStart, ConfigChange, Notification). For Stop, SubagentStop, UserPromptSubmit, TaskCompleted, PreCompact, PostCompact, and SessionStart, the matcher field is silently ignored — the hook fires unconditionally on every occurrence of that event.

**Conclusion:** Branch A (add matchers to gate stop-guard/compact-hint to interactive sessions) is **not viable**. Branch B (document the platform constraint) is the correct path.

**Approach:** Add a comment to the Stop section in `hooks.json` recording the finding. No hook code changes needed — the existing hooks already implement fast early-exit guards internally (e.g., `is_interrupt`, `compact_hint_threshold`) to handle non-interactive or trivial invocations gracefully.

**Components:**
- `hooks/hooks.json` — add `_stop_matcher_note` comment key inside the Stop entry documenting the constraint
- `zie-framework/decisions/` — optional ADR recording the investigation (no behaviour change, so low priority)

**Data Flow:** Unchanged. All Stop hooks continue to fire on every stop event and rely on their own internal guards to no-op when appropriate.

**Edge Cases:**
- A future Claude Code version may add matcher support for Stop events. When that happens, `stop-guard.py` (spawns a git subprocess) and `compact-hint.py` (reads context usage) are the two hooks worth gating to interactive sessions only.
- `session-learn.py` and `session-cleanup.py` run in background (`"background": true`) and are already low-overhead; gating them provides minimal benefit even if matchers become available.

**Out of Scope:**
- Changing hook logic or adding new internal guards — hooks already exit cleanly on non-applicable stops.
- Investigating matcher semantics for other non-tool events (PreCompact, SubagentStop, TaskCompleted) — separate concern.
