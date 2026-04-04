# Fix Sprint ROADMAP Phase Rebind

## Problem

`/sprint` reads `ROADMAP.md` at pre-flight (step 3), then re-reads it after Phase 1 ("reload ROADMAP"), and re-reads it again at Phase 3 ("Read Ready items from ROADMAP"). Phase 2 and 3 could reuse the Phase 1 reload result unless a mutation actually occurred.

## Motivation

Across a 5-phase sprint, ROADMAP is read at minimum 3 times sequentially. Binding `roadmap_post_phase1` and threading it into Phase 2 and 3 avoids redundant reads for items that haven't changed, reducing context overhead on long sprints.

## Rough Scope

- In: bind `roadmap_post_phase1` after Phase 1 reload; Phase 2 and 3 consume that binding unless a known mutation (spec/plan agent wrote to ROADMAP) occurred
- Out: no behavior change; re-read still triggered when phases mutate ROADMAP
