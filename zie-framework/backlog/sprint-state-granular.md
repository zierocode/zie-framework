# sprint-state-granular — Per-Item .sprint-state Updates in Phase 2

## Problem

Currently `.sprint-state` is written only at phase boundaries (after Phase 1 completes, after Phase 2 completes, etc.). When context overflows mid-Phase 2 (during implementation of item N of M), the state file still shows `phase: 2` with all remaining_items, losing track of which specific items already finished. On resume, the user must manually determine where to pick up, or items get re-implemented.

## Motivation

Sprint context overflow during Phase 2 is a common occurrence — impl generates substantial conversation history. The recovery should be seamless: resume in a new session, run `/sprint`, and it picks up from the exact item that was interrupted, not from the beginning of Phase 2.

## Rough Scope

- Modify `commands/sprint.md` Phase 2 loop: after each item completes successfully, rewrite `.sprint-state` with updated `remaining_items` (remove the just-completed slug)
- On resume: if `phase: 2` and `remaining_items` is a subset of `items`, skip already-done items and continue from the first remaining slug
- No changes to Phase 1, 3, or 4 state tracking (those are already at the right granularity)
