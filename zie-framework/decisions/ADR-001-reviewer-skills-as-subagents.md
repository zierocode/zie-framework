# ADR-001: Reviewer Skills as Dispatched Subagents

Date: 2026-03-23
Status: Accepted

## Context

The 6-stage SDLC pipeline (D-007) requires quality gates at spec, plan, and
implementation handoffs. Two implementation options were considered:

1. **Inline review** — the same agent that wrote the artifact reviews it
2. **Subagent dispatch** — a fresh agent reviews the artifact in isolation

Inline review is faster but suffers from confirmation bias: the agent that
wrote the spec tends to approve its own work without surfacing real gaps.

## Decision

Reviewer skills (`spec-reviewer`, `plan-reviewer`, `impl-reviewer`) are
dispatched as subagents with precisely crafted context — the artifact path and
relevant input, never the full session history.

Each reviewer uses a fixed checklist (8–9 items) and returns a binary verdict:
`✅ APPROVED` or `❌ Issues Found` with file:line references. Max 3 iterations
before surfacing to human.

## Consequences

- Fresh subagent context catches issues the author missed (no confirmation bias)
- Checklist-driven output makes feedback actionable, not vague
- 3-iteration cap prevents infinite loops on genuinely ambiguous specs
- Slight latency increase per task (one extra agent dispatch per handoff)
- Reviewer skills must be kept narrow — if they grow too opinionated, they
  become blockers rather than helpers
