---
tags: [chore]
---

# Phase/Step Explanatory Prose Cleanup

## Problem

Phase headers like `## Phase 2 — Parallel Internal Analysis` already describe what happens.
The 2–3 explanatory sentences that follow ("Spawn 5 parallel agents via Agent tool…") add
nothing because the first imperative step says the same thing. This pattern repeats across
zie-audit, sprint, retro, release, and other commands — ~500 words of decorative prose.

Additionally, "Never do X" rules in tdd-loop and debug are duplicated both in the rules
section and inline in each phase step, adding ~200 more words.

## Motivation

Removing explanatory-but-redundant prose reduces tokens per command invocation with no
functional loss. The model doesn't need sentiment reassurance — it needs clear imperatives.
Combined savings: ~600–700 words (~4% of corpus) with very low risk of test failures.

## Rough Scope

- Remove explanatory paragraph under each phase header where the first step says the same thing
- Consolidate "Never do X" rules in tdd-loop and debug into a single block; remove inline repetitions
- Affected files: zie-audit/SKILL.md, sprint.md, retro.md, release.md, tdd-loop/SKILL.md, debug/SKILL.md
- Run `make test-unit` gate after each file to catch any broken test assertions
