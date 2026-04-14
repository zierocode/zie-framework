---
tags: [feature]
---

# Sprint Context Passthrough — Phase 1→2→3 Bundle

## Problem

Phase 1 spawns Skill calls; Phase 2 calls `make zie-implement` subprocess; each re-reads approved plans from disk. Context lost at phase boundaries; subprocess loses in-session cache; ROADMAP re-parsed 3× per sprint.

## Motivation

Pass context bundle between phases eliminates redundant disk reads. ~4.5w tokens saved per 5-item sprint.

## Rough Scope

**In:**
- `commands/sprint.md` Phase 1 — write `.zie/sprint-context.json` with specs+plans
- `commands/sprint.md` Phase 2/3 — read from bundle instead of disk
- `.zie/sprint-context.json` — sprint bundle (specs+plans)

**Out:**
- Individual item context (unchanged)

<!-- priority: HIGH -->
<!-- depends_on: unified-context-cache -->
