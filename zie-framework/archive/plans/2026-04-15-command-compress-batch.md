---
date: 2026-04-15
status: approved
slug: command-compress-batch
---

# Implementation Plan — command-compress-batch

## Steps

1. **Compress sprint.md (~20%)** — Convert pre-flight checklist to table; collapse Phase 1-4 headers into short labeled blocks; replace python/json code blocks with one-liner references; inline retry logic into parenthetical notes; merge "All means ALL" and "Clarity scoring" into a compact table.

2. **Compress status.md (~15%)** — Merge Steps 1-8 into a numbered pipeline with inline parenthetical logic; collapse knowledge drift + test health checks into a 2-row summary table; fold pipeline-stage indicator into the main status table as a single row.

3. **Compress retro.md (~15%)** — Convert ADR gate logic to a decision table (has `<!-- adr: required -->`? → full ADRs | no → summary only); collapse self-tuning proposals into a 3-row condition table; inline done-rotation algorithm into a compact numbered list.

4. **Compress release.md (~20%)** — Convert gate sequence (5 gates) into a single table with columns gate/test/action; collapse version-bump semver rules into a 3-row table; merge steps 1-10 into a numbered pipeline with inline bash references.

5. **Verify word counts** — Run `wc -w` on all 4 files; confirm each meets its target reduction.

## Tests

- `make test-fast` — all existing tests still pass (commands are markdown, no logic change)
- Visual diff review — confirm no functional behavior removed (all flags, phases, gates present)
- Word count check — each file within target range

## Acceptance Criteria

- [ ] Each of the 4 files reduced by stated percentage (sprint ~20%, status ~15%, retro ~15%, release ~20%)
- [ ] All functional behavior preserved: flags, phases, gates, steps identical in effect
- [ ] `make test-fast` passes
- [ ] No new files created — only existing files edited