# Backlog: SubagentStart — Inject SDLC Context into Every Subagent

**Problem:**
When zie-implement or zie-plan spawns an Explore or Plan subagent to research
the codebase, that subagent has no SDLC context. It doesn't know what feature
is active, what task it should focus on, or what ADRs constrain the design.
The subagent researches generically instead of purposefully.

**Motivation:**
`SubagentStart` fires when any subagent is spawned and supports
`additionalContext` injection. Injecting SDLC state (active feature, current
task, relevant ADRs) means every research subagent searches with purpose.

**Rough scope:**
- New hook: `hooks/subagent-context.py` (SubagentStart event)
- Matcher: `Explore|Plan` (only inject into research agents, not all)
- Read: ROADMAP Now lane, current task from plan file, ADR count
- Output: `additionalContext` with feature slug, task description, constraints
- Fast: file reads only, no subprocess
- Register in `hooks/hooks.json`
- Tests: correct context injected, non-matching agents not affected
