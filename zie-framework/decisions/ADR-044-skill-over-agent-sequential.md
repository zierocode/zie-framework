---
status: Accepted
date: 2026-04-04
---

# ADR-044 — Use Skill Invocation Instead of Agent Spawning for Sequential Workflow Steps

## Status
Accepted

## Context
/zie-sprint Phase 3 and /zie-implement TDD loop were spawning Agent(subagent_type="general-purpose", run_in_background=True) for sequential tasks — this adds ~5k token overhead per spawn and loses the parent's conversation context.

## Decision
Replace Agent spawning with direct Skill() invocation for sequential, in-process workflow steps. Specifically: /zie-sprint Phase 3 now invokes Skill(zie-framework:zie-implement) directly; /zie-implement task loop now invokes Skill(zie-framework:tdd-loop) instead of repeating inline TDD prose. Reserve Agent for: parallel file-writing tasks, background/async work, external research, tasks that intentionally run in isolation.

## Consequences
**Positive:** No subprocess overhead for sequential steps, full context access within parent, inline execution is faster and deterministic.
**Negative:** Cannot parallelize Skill invocations (by design for WIP=1).
**Neutral:** tdd-loop skill becomes the canonical TDD reference; inline prose removed from zie-implement.md.

## Alternatives Considered
- Keep Agent spawning but reduce prompt size to lower the ~5k token overhead per spawn.
- Use TaskCreate/TaskUpdate without Agent to coordinate sequential steps while preserving some isolation.
