---
tags: [feature]
---

# Status Roadmap Content Summary

## Problem

The `/status` command reads ROADMAP but doesn't surface the content of backlog items, specs, or plans. Users need to manually check each file to understand what's in the pipeline.

## Rough Scope

**In:**
- Add content summary to `/status` — show backlog Problem excerpt for each item in Next/Ready/Now lanes
- Show spec status (exists/not yet, filename)
- Show plan status (exists/not yet, filename)
- Keep output concise — first 1-2 lines of Problem section only

**Out:**
- Full file contents in status output (too verbose)
- Changes to ROADMAP format itself

## Priority

LOW