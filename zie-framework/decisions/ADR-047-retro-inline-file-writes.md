# ADR-047: Retro ADR + ROADMAP Writes Are Inline, Not Agents

**Status:** Accepted  
**Date:** 2026-04-04

## Context

`/zie-retro` previously spawned two background agents to write ADR files and
update the ROADMAP Done section. Each agent spawn costs context setup, tool
invocation overhead, and 2–5s latency. The writes are sequential file
operations that do not benefit from parallelism.

## Decision

Replace both agent spawns with inline `Write` and `Edit` tool calls in the
retro command flow. ADR composition and ROADMAP update run sequentially in the
same context as the retro, with progress printed per ADR.

## Consequences

**Positive:**
- Eliminates 2 subagent spawns per retro (~10–20k tokens overhead removed).
- Simpler mental model — the retro command is a single linear flow.
- No `run_in_background` coordination or "await both" synchronization step.

**Negative:**
- Retro takes slightly longer in wall-clock time (was parallel, now sequential).
  In practice this is negligible — ADR writes are small files.

**Neutral:**
- `retro-format` skill deleted (was only used by the retired agent approach).
- Test suite updated: agent-centric assertions replaced with inline-write assertions.

## Alternatives

- Keep agents: better for very large ADR batches (>10), but rare in practice.
- Hybrid: inline for ≤3 ADRs, agents for larger batches. Premature optimization.
