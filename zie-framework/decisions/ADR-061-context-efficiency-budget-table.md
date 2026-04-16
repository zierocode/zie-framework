# ADR-061 — Context Efficiency: Per-Agent Budget Table Supersedes ADR-046

**Date:** 2026-04-11
**Status:** Accepted
**Supersedes:** ADR-046

## Context

ADR-046 added an early-exit guard to `subagent-context.py` restricting context
injection to Explore and Plan agent types:

```python
if not re.search(r'Explore|Plan', agent_type): sys.exit(0)
```

This was a blunt instrument that correctly solved the immediate problem (don't
spam reviewers with project state) but made it impossible to add per-agent
differentiation without modifying the guard.

## Decision

Replace the binary Explore/Plan guard with an `AGENT_BUDGETS` dispatch table
that explicitly maps each agent type to an inject/skip decision:

```python
AGENT_BUDGETS = {
    "spec-review": True,
    "plan-review": True,
    "impl-review": True,
    "resync":        True,
    "Explore":       True,
    "Plan":          True,
    "brainstorm":    False,  # skill has own Phase 1 discovery
}
_DEFAULT_INJECT = False  # conservative default: don't inject unknown types
```

The table also enables future per-agent payload differentiation (what context
each agent receives) by expanding the value from bool to a bundle descriptor.

Additionally, a session-scoped cache flag (`project_tmp_path("session-context-{session_id}", project)`)
prevents re-injecting the same project state on every SubagentStart event
within a single session.

## Consequences

- All current Explore/Plan behaviour is preserved (both map to True in the table).
- New agent types (brainstorm) can opt out of injection without code changes.
- Session cache reduces redundant context injection for multi-agent sessions.
- Unknown agent types receive a conservative default (no inject) rather than accidental context.
- ADR-046 is superseded; its guard is removed from `subagent-context.py`.
