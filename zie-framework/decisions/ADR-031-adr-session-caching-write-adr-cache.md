# ADR-031: ADR Session Cache — write_adr_cache / get_cached_adrs Pattern

Date: 2026-03-30
Status: Accepted

## Context

Parallel fan-out agents (e.g., in zie-retro) all need access to the same ADR list. Without coordination, each agent independently reads the decisions directory, producing redundant I/O and inconsistent snapshots if ADRs change mid-session.

## Decision

Introduce a write_adr_cache / get_cached_adrs pattern: the first agent in the fan-out reads and writes the ADR cache; all subsequent agents call get_cached_adrs to read from it. The cache is scoped to the session.

## Consequences

**Positive:** Eliminates redundant ADR reads across parallel agents; all agents operate on a consistent snapshot.
**Negative:** The first agent becomes a blocking dependency — parallel agents cannot start until the cache is written. Cache is stale if ADRs are added mid-session.
**Neutral:** Cache invalidation is manual (session-scoped); no eviction logic needed for current use cases.
