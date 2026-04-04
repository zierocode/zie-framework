# Lean SubagentStop — No Matcher Support — Design Spec

**Problem:** `SubagentStop` in `hooks.json` has no `matcher` field, so the hook
fires on every subagent completion in every project. Python startup + utils import
+ cwd check incurs overhead on each fire, even in non-zie-framework projects.
The existing `_stop_matcher_note` comment in `hooks.json` is scoped only to the
`Stop` event block — it does not address whether `SubagentStop` supports matchers.

**Approach:** Investigate whether `SubagentStop` supports matchers in the Claude
Code plugin spec. Based on findings: (a) if supported, add a matcher such as
`"Explore|Plan|spec-reviewer|plan-reviewer|impl-reviewer"` to filter to
zie-framework-scoped agents; (b) if not supported, update the hooks.json comment
to explicitly document this for `SubagentStop` and keep the in-hook cwd guard as
the sole filter. Option (b) is the expected outcome given Claude Code docs
indicate matcher support is limited for async/stop-class hooks, but the
investigation is required to confirm. No code changes to `subagent-stop.py`
itself — the two-tier guard is already correct and minimal.

**Components:**
- `hooks/hooks.json` — add matcher to `SubagentStop` block if supported; update
  comment if not
- `zie-framework/decisions/` — new ADR documenting the SubagentStop matcher
  investigation result
- `tests/unit/test_hooks_json.py` or `test_hooks_subagent_stop.py` — add
  assertion covering the documentation/comment presence in hooks.json

**Data Flow:**
1. SubagentStop event fires (any project, any agent type)
2. If matcher supported: Claude Code filters before spawning Python — overhead
   eliminated for non-zie-framework projects
3. If matcher not supported: Python starts, Tier 1 guard reads `CLAUDE_CWD`,
   checks `(cwd / "zie-framework").is_dir()`, exits 0 immediately if absent
4. Either path: hook result is the same — non-zie-framework projects are never
   affected by hook logic

**Edge Cases:**
- SubagentStop fires in a project that has a `zie-framework/` dir but is not a
  zie-framework plugin project — cwd guard catches this (existing behavior,
  unchanged)
- Matcher syntax differs from SubagentStart (which uses `"Explore|Plan"`) — must
  verify what field Claude Code matches against for SubagentStop events (agent_type
  vs. some other field)
- Claude Code silently ignores an unsupported matcher field — so adding one when
  unsupported is harmless but misleading; the comment is the only artifact that
  matters in that case

**Out of Scope:**
- Changes to `subagent-stop.py` logic or data structure
- Adding new subagent log fields or altering the JSONL format
- Optimizing other hooks' startup cost
- Changing `SubagentStart` matcher (already correct with `"Explore|Plan"`)
