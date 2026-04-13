---
approved: true
approved_at: 2026-04-13
backlog: backlog/sprint-phase2-resilience.md
---

# sprint-phase2-resilience — Design Spec

## Problem

Sprint Phase 2 has two resilience gaps that cause context-overflow failures to be unrecoverable:
1. `.sprint-state` is written only at phase boundaries — mid-phase overflow loses per-item progress
2. Accumulated impl history across items consumes context budget before Phase 3

## Goals

- G1: Context overflow mid-Phase 2 → resume picks up from the interrupted item, not from scratch
- G2: Per-item compact reduces context accumulation, lowering overflow probability

## Non-Goals

- Not changing Phase 1, 3, or 4 state granularity
- Not changing how impl agents work
- Not adding new configuration keys

## Design

### Change 1 — Granular .sprint-state after each item

Current Phase 2 loop writes state only after ALL items complete. New behavior:

After step 3 (`[impl N/total] <slug> ✓`):
```
Update .sprint-state: remaining_items = remaining_items - [<slug>]
```

Resume logic (pre-flight step 7): if `phase=2`, use `remaining_items` as the item list — skips already-completed slugs. Print:
```
[resume] Phase 2 — skipping completed: <done_slugs>
         resuming from: <next_slug>
```

### Change 2 — /compact between Phase 2 items

After each item (except the last) in the Phase 2 loop, before starting next item:
```
/compact
print: [compact] context cleared after <slug>
```

NOT before the first item (context is fresh after Phase 1 compact).
NOT after the last item (Phase 2 → Phase 3 already has a compact checkpoint).

## Acceptance Criteria

- AC1: `commands/sprint.md` Phase 2 loop updates `.sprint-state` after each item
- AC2: Resume logic at pre-flight step 7 skips completed slugs based on `remaining_items`
- AC3: `/compact` + print statement appears between items (not before first, not after last)
- AC4: Tests verify all three structural patterns in sprint.md
- AC5: No new Python files, no new config keys — markdown edit only
