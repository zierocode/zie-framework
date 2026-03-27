---
id: artifact-archive-strategy
title: SDLC artifact archiving — prevent backlog/specs/plans bloat
priority: medium
created: 2026-03-27
source: deep-analysis-2026-03-27
---

## Problem

SDLC artifacts accumulate with no pruning strategy:
- `zie-framework/backlog/` — 114 items, 460KB (includes completed items)
- `zie-framework/specs/` — 109 specs, 644KB (includes shipped specs)
- `zie-framework/plans/` — 100+ plans (includes shipped plans)

These directories grow unbounded per release cycle, making PROJECT.md harder to navigate
and inflating context bundles passed to reviewer agents.

## Motivation

Keep the working SDLC state lean. Completed artifacts should be preserved (for history) but
moved out of the active working directories so context bundles stay small.

## Acceptance Criteria

- [ ] `zie-framework/archive/` directory created with `backlog/`, `specs/`, `plans/` subdirs
- [ ] `/zie-release` moves shipped backlog items + their specs/plans to `archive/` post-release
- [ ] `make archive` target added for manual archiving
- [ ] Active directories contain only: open backlog items + their associated specs/plans
- [ ] CHANGELOG entry links to archive for historical reference
- [ ] Archive is NOT loaded into context bundles (reviewer agents ignore `archive/`)

## Scope

- `commands/zie-release.md` — add archive step post-merge
- `Makefile` — `make archive` target
- `zie-framework/` — create archive directory structure
- Context bundle definitions in reviewer skills (exclude archive/)
