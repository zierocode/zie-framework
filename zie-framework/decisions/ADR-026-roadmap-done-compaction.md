## ADR-026: ROADMAP Done Section Auto-Compaction

**Date:** 2026-03-27
**Status:** Accepted (Compressed from ADR-000-summary.md)

## Context

The ROADMAP.md Done section grows without bound. After many releases the
section exceeds 20 entries, making the file harder to scan and adding noise
to every context read that ingests ROADMAP.md.

## Decision

Add `compact_roadmap_done()` to `hooks/utils.py`. When the Done section has
more than 20 entries and some are older than 6 months, compact the oldest
entries into a single archive summary line of the form
`<!-- archived N items older than YYYY-MM -->`.

## Consequences

- Done section stays compact; recent history is immediately visible.
- Oldest entries are summarised, not deleted — audit trail preserved.
- `compact_roadmap_done()` is called by `/zie-retro` after writing the Done
  section update.
