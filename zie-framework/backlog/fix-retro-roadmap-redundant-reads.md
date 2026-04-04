# Fix Retro ROADMAP Redundant Reads

## Problem

`/retro` reads `ROADMAP.md` three times: once in pre-flight (step 3, caches Now/Done/Next lanes), again inside "Update ROADMAP Done inline", and again in "Done-rotation". The pre-flight read already has the full content but it isn't passed forward.

## Motivation

ROADMAP can be 200–400 lines. Three reads consume ~1,200 lines of context redundantly per retro session. Binding `roadmap_raw` at pre-flight and threading it through all downstream sections eliminates this waste.

## Rough Scope

- In: bind `roadmap_raw` at pre-flight step 3; pass to Done-write and Done-rotation sections
- Out: no behavior change to retro output
