---
date: 2026-04-15
status: approved
slug: backlog-dedup-expand
---

# Backlog Dedup and Expand Check

## Problem

When adding new backlog items, `/backlog` only checks Next lane slugs for token overlap. It misses duplicates in Ready and Done lanes. When a true duplicate is found, the existing item should be expanded with new context rather than creating a new one.

## Solution

Extend the duplicate check in `commands/backlog.md` to cover all ROADMAP sections (Next, Ready, Done) using `parse_roadmap_section_content` from `utils_roadmap.py`. Add two new steps after the existing token-overlap check:

- **3d (Done check)**: scan Done items for title overlap; warn if similar
- **3e (Expand check)**: if a duplicate is found, offer to expand the existing item instead of creating a new one — append `## Additional Scope` section with the new context

## Rough Scope

**In:** update `commands/backlog.md` steps 3d/3e, reuse `parse_roadmap_section_content` for section scanning, add expand logic to `/backlog` skill

**Out:** auto-merge without confirmation, slug format changes, new Python hook

## Files Changed

- `commands/backlog.md` — add steps 3d, 3e