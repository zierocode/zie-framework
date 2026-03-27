# ADR-023: SDLC Artifact Archive Strategy
Date: 2026-03-27
Status: Accepted

## Context
zie-framework accumulates backlog items, specs, and plans over time. Shipped
artifacts remain in active directories (backlog/, specs/, plans/) indefinitely,
creating noise in reviewer context bundles and slowing glob reads. The release
step already deletes shipped artifacts (Step 4 in /zie-release), but this is
destructive — git history preserves content but local working tree loses files
without a trace for quick reference.

## Decision
Introduce `zie-framework/archive/` with three subdirectories: `archive/backlog/`,
`archive/specs/`, `archive/plans/`. Add `make archive` target that moves Done-lane
items (matched by slug) to archive after release. `zie-release.md` calls `make archive`
post-merge. Archive dirs are excluded from reviewer context bundles (reviewers read
from active dirs only). Slug matching (not exact filename) handles date-prefixed files.

## Consequences
- Active dirs contain only in-flight work — cleaner reviewer context
- Shipped artifacts queryable locally in archive/ without git log
- `make archive` is idempotent (skip if already archived)
- Reviewer skills must continue reading from active dirs only (no archive reads)
- Archive dirs tracked in git via .gitkeep; content excluded via .gitignore if desired
