# Backlog: Add project guard to subagent-stop or add SubagentStop matcher

**Problem:**
SubagentStop hook in hooks.json has no matcher field — fires on every subagent
completion in any project. The hook does a `if not (cwd / "zie-framework").is_dir():
sys.exit(0)` guard, so it exits cleanly in non-plugin projects. But Python startup
+ utils import + cwd check runs on every single subagent stop in every project.
SubagentStart uses `matcher: "Explore|Plan"` but SubagentStop has no equivalent.

**Motivation:**
Claude Code docs note that Stop hooks have limited matcher support. However,
SubagentStop may have different constraints. If a matcher can be added, it would
eliminate the Python startup overhead for non-zie-framework projects entirely.

**Rough scope:**
- Investigate whether SubagentStop supports matchers in Claude Code plugin spec
- If supported: add appropriate matcher to filter to zie-framework contexts
- If not: document why in hooks.json comment (already has "Stop hooks have no
  matcher support" comment — verify this is still accurate for SubagentStop)
- Tests: subagent in non-zie-framework dir → hook exits immediately (already tested,
  confirm coverage)
