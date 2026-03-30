# ADR-033: Parallel Release Gates Fan-Out in zie-release

Date: 2026-03-30
Status: Accepted

## Context

zie-release previously ran docs-sync and validation gates sequentially. Gates 2, 3, and 4 have no ordering dependency on each other — only Gate 1 must complete first. Sequential execution left significant wall-clock time on the table.

## Decision

docs-sync spawns before Gate 1. After Gate 1 passes, Gates 2, 3, and 4 spawn simultaneously as parallel agents. Each gate reports its result independently.

## Consequences

**Positive:** Release wall-clock time is reduced proportional to the slowest parallel gate rather than the sum of all gates. Multiple gate failures surface in one pass instead of one at a time.
**Negative:** Error output from simultaneous failures may be harder to read; callers must handle multiple concurrent failure reports.
**Neutral:** Gate ordering constraints must be explicitly documented — adding a new gate requires determining whether it belongs in the parallel or sequential phase.
