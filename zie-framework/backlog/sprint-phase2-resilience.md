# sprint-phase2-resilience — Granular State + Per-Item Compact in Phase 2

## Problem

Sprint Phase 2 (impl) has two resilience gaps. First, `.sprint-state` is written only after ALL items complete, so a context overflow mid-phase loses track of which items already finished — resume must re-implement from scratch. Second, each item's conversation history accumulates across the loop: by item 2, context already carries item 1's full impl output, reducing headroom for subsequent items and increasing overflow risk before Phase 3 (release).

## Motivation

Sprint context overflow during Phase 2 is the most common failure mode. The two fixes complement each other: per-item compact prevents overflow (preventative), and granular state enables seamless recovery when overflow still occurs (resilience). Together they handle 95%+ of overflow scenarios.

## Rough Scope

Modify `commands/sprint.md` Phase 2 loop only:
1. **State granularity**: after each item completes, rewrite `.sprint-state` with that slug removed from `remaining_items`. On resume, skip slugs absent from `remaining_items`.
2. **Per-item compact**: after each item's impl+commit (except the last), run `/compact` and print `[compact] context cleared after <slug>`.
<!-- consolidates: sprint-state-granular + sprint-compact-per-item -->
