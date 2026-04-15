---
tags: [feature]
---

# Backlog Dedup and Expand Check

## Problem

When adding new backlog items, `/backlog` doesn't check for duplicates against existing items (both in Next and Done lanes). Similar ideas get added multiple times, creating clutter. When a duplicate is found, the existing item should be expanded with new context rather than creating a new one.

## Rough Scope

**In:**
- Add dedup check in `/backlog` skill — compare new item against existing Next+Ready+Done items using title similarity and content hashing
- If duplicate found, expand existing item with new context (append `## Additional Scope` section)
- If similar-but-different, link them (add cross-reference in both items)
- Update `/backlog` command (commands/backlog.md) with new steps 3d (Done check) and 3e (Expand check)

**Out:**
- Automatically merging items without user confirmation
- Changing the slug format or naming convention

## Priority

MEDIUM