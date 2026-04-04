# ADR-052 — Bind-Once Pattern for Session-Scoped Variables

**Status:** Accepted

## Context

Commands and skills were re-reading the same files multiple times in a single
execution flow — `.config` up to 3× in `/release`, `ROADMAP.md` up to 3× in
`/retro`, and ADR context repeatedly in reviewer skills. Each re-read costs
tokens and latency with no new information gained, since the files do not
change mid-session.

## Decision

Session-scoped variables (config, ROADMAP content, ADR cache, context bundle)
are read **once** at pre-flight and bound to named variables. All downstream
sections, gates, and skills reference the bound variable — never re-read the
same file path inline. Commands document this binding at pre-flight:
`Read X → bind as var_name (reused by all downstream sections, no second read)`.

## Consequences

**Positive:** Eliminates O(N) redundant reads where N = sections referencing
the same file. Reduces token cost and latency proportionally. Pre-flight
section becomes the single source of truth for what is in scope.

**Negative:** Pre-flight becomes load-bearing — a missing or stale bind
propagates through all downstream steps.

**Neutral:** Pattern requires discipline in prose: downstream sections must
reference the variable name, not re-state the file path.

## Alternatives

- Per-section reads (rejected: O(N) cost, no benefit)
- Caching layer in hooks (considered: overkill for prose-driven commands)
