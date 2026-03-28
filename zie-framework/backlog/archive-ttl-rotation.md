# Archive TTL Rotation — Prune Cold Storage

## Problem

`zie-framework/archive/` grows linearly with no upper bound — ~3 files per feature
(backlog + spec + plan). Currently 166 files after 8 days of active development.
Projected ~7,500 files after 1 year. While archive content never loads into Claude's
context, the directory becomes impractical to navigate and adds noise to `git log`.

## Motivation

Archive exists as a safety net for recently shipped work (rollback reference, audit
trail). Items older than 90 days have no realistic rollback use — git history is
the authoritative record. Pruning old archive entries reduces repo noise without
losing any information.

## Rough Scope

- Add `make archive-prune` target: delete archive files (backlog/specs/plans) with
  mtime > 90 days, print count of files removed
- Add `make archive-prune` call to `/zie-retro` post-release step (automated, not
  just a manual target)
- Guard: never prune if `archive/` has fewer than 20 total files (avoid pruning
  young projects)
- Document in CLAUDE.md under Development Commands
- Tests: prune removes correct files, guard prevents premature pruning
