---
tags: [chore]
---

# Command Map Pre-Load — cache in plugin-state

## Problem

Extracts command list from SKILL.md on every SessionStart; regex parse of 800w file. Static data parsed every session; command list changes only on releases.

## Motivation

Cache command map in plugin-state; invalidate on SKILL.md mtime change. ~300 tokens saved per session.

## Rough Scope

**In:**
- `hooks/session-resume.py` lines 55-70 — add cache
- `.zie/cache/plugin-state.json` — command map cache
- Invalidation on SKILL.md change

**Out:**
- Command parsing logic (cached, not re-run)

<!-- priority: LOW -->
<!-- depends_on: unified-context-cache -->
