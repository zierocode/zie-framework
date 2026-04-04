# ADR-046: Subagent Context Scoped by Agent Type

**Status:** Accepted  
**Date:** 2026-04-04

## Context

`subagent-context.py` read the most-recent plan file and extracted the first
incomplete task for every SubagentStart event (Explore and Plan agents alike).
Explore agents (read-only codebase exploration) have no active task to surface;
reading the plan file wastes I/O and injects irrelevant `Task:` noise into
their context.

## Decision

Guard the plan file read with `if re.search(r'Plan', agent_type, re.IGNORECASE)`.
Explore agents receive `Active: {slug} | ADRs: {count}` only — no `Task:` field.
Plan agents retain the full payload including the `Task:` field.

## Consequences

**Positive:**
- Explore agents skip one disk read and a loop over all plan lines per spawn.
- Context payload is right-sized: Plan agents get task context; Explore agents don't.
- Easier to reason about hook behavior — each agent type gets exactly what it needs.

**Negative:**
- If a new agent type needs task context, the guard must be extended explicitly.

**Neutral:**
- Existing tests updated to use `"Plan"` for task-extraction assertions.
- New tests added to assert `"Task:"` absent for Explore agents.

## Alternatives

- Always read plan file: simpler guard logic but wastes I/O on Explore agents.
- Agent-specific hooks: cleaner in theory but requires duplicating the ROADMAP read logic.
