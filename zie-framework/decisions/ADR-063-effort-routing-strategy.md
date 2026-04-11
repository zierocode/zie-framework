---
status: Accepted
date: 2026-04-12
---

# ADR-063 — Effort Routing Strategy for Sonnet 4.6 Medium

## Status

Accepted

## Context

zie-framework runs on Sonnet 4.6 with `effort: medium` globally. Several skills and commands
previously declared `effort: high`, which no longer matches the runtime and wasted tokens by
requesting max computation on tasks that complete correctly at medium effort.

## Decision

Effort levels follow this routing table:

| Level | When to use | Examples |
|-------|-------------|---------|
| `low` | Single-step reads, status checks, simple edits | debug, tdd-loop, verify, status |
| `medium` | Multi-step with branching, requires synthesis | implement, spec-design, brainstorm, zie-audit |
| `high` | Reserved for orchestrators spanning full SDLC cycles | sprint (only) |

`brainstorm` and `spec-design` lowered from `high` → `medium`: both complete correctly at medium
effort on Sonnet 4.6 and the context budget per phase is well within medium-effort window.

`sprint` retains `effort: high` as it orchestrates a full spec→plan→implement→release→retro
pipeline and must hold context across all phases.

## Consequences

**Positive:** Reduced token cost per brainstorm/spec session. Faster iteration.
**Negative:** If a brainstorm or spec becomes unusually complex, the user may need to break it
into sub-tasks rather than relying on max effort to power through.
**Neutral:** Effort field is advisory — the actual effort level is controlled by user's global
Claude Code setting.
