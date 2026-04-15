---
tags: [feature]
---

# Backlog Dedup and Expand Check

## Problem

The `/backlog` command currently checks for slug collisions (step 3c: token-overlap) but does not check:
1. Whether the idea was already shipped (exists in Done section of ROADMAP.md)
2. Whether a related backlog item already exists that should be expanded instead of creating a new one

This leads to duplicate items like `config-session-cache` and `audit-uncached-config-reads` being created independently for the same problem, or items being created for features that were already shipped.

## Motivation

A healthy backlog should have no duplicates and no re-shipped items. Expanding an existing item is better than creating a new one — it keeps context consolidated and reduces management overhead.

## Rough Scope

**In:**
- Add step 3d (Done check): grep `- [x]` lines in ROADMAP.md for slug or keyword overlap → warn "Already shipped: [Done item]. Reopen instead?" and stop
- Add step 3e (Expand check): if an existing backlog item shares ≥2 tokens with the new slug → suggest "Expand existing item [slug] instead?" with option to append scope to existing file
- If user chooses to expand: open the existing backlog file, append new content under a new `## Additional Scope` section, update tags if needed — do NOT create a new file
- Update `/backlog` command (commands/backlog.md) with new steps

**Out:**
- Automatically merging items without user confirmation
- Changing the slug format or naming convention