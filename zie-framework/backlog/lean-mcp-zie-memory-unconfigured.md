# Backlog: Add zie-memory MCP availability check before brain calls in commands

**Problem:**
Commands (backlog.md, release.md, plan.md, implement.md, retro.md, fix.md, init.md)
reference `mcp__plugin_zie-memory_zie-memory__recall`, `__remember`, `__downvote_memory`
without checking if the plugin is installed. When zie-memory is not in settings.json,
these MCP tool calls produce "tool not found" errors visible to Claude mid-command.
The hooks (session-learn.py, wip-checkpoint.py) correctly gate on `zie_memory_enabled`
config, but commands do not.

**Rough scope:**
- Add a pre-flight check in each brain-calling command: "if zie_memory_enabled not
  in .config → skip brain steps, continue without them"
- Or: add a conditional wrapper in the command prose: "only if brain: enabled in
  /status output"
- Align with how hooks already handle this (graceful degradation pattern)
- Tests: command flow with zie_memory_enabled=false skips MCP calls without error
