---
tags: [feature]
---

# Show ROADMAP Content in /status

## Problem

The `/status` command shows "Next: 9 queued" and "Done: 82 shipped" as counts only — it doesn't surface the actual backlog item names. Users who want to see what's queued must manually scan the `zie-framework/backlog/` directory instead of reading from the ROADMAP they already maintain.

## Motivation

ROADMAP.md is the single source of truth for project state. `/status` should give enough context to decide what to work on next without a second lookup. Surfacing backlog item names (especially top-priority ones) directly in `/status` eliminates a round-trip to the filesystem.

## Rough Scope

**In:**
- Show top N backlog items from ROADMAP Next section in `/status` output
- Show most recent Done items from ROADMAP Done section (last 3-5)
- Respect existing targeted-read pattern (grep line numbers, read slice — don't load full file)

**Out:**
- Full backlog listing (that's what `/next` is for)
- Changing ROADMAP format or structure