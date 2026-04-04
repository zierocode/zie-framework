## ADR-023: SDLC Artifact Archive Strategy

**Date:** 2026-03-27
**Status:** Accepted (Compressed from ADR-000-summary.md)

## Context

Backlog items, specs, and plans accumulate in their respective directories
over time. Old artifacts that are already shipped clutter the workspace and
add noise to glob-based context reads.

## Decision

Introduce `zie-framework/archive/` with `backlog/`, `specs/`, and `plans/`
subdirectories. `make archive` moves Done-lane items' associated artifacts
post-release. Archive directories are excluded from reviewer context bundles
to prevent stale context injection.

## Consequences

- Active workspace stays lean; only current-cycle artifacts are visible.
- Archived artifacts are preserved for historical reference.
- `make archive-prune` removes archive files older than 90 days (guard:
  ≥20 files must exist before pruning runs).
