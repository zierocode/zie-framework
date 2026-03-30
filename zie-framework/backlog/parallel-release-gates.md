# Parallel Release Gates

## Problem

/zie-release runs test gates sequentially (unit → integration → e2e → visual → docs-sync) even though Gates 2, 3, 4 and the docs-sync quality check have no dependencies on each other. After Gate 1 (unit) passes, the remaining checks could all run in parallel but instead execute one at a time, adding unnecessary wall-clock time to every release. Similarly, /zie-retro fires two retro-format agent calls sequentially despite them writing to different files with no data dependency.

## Motivation

Release is the one command users run most carefully and most want to be fast. Currently after Gate 1 passes, users wait for integration → e2e → docs-sync sequentially. All three could run simultaneously. The same applies to the /zie-retro ADR write + ROADMAP update parallel agents — they write to different paths and can safely run concurrently. These are pure speed wins requiring no logic changes, only execution order changes.

## Rough Scope

**In Scope:**
- /zie-release: after Gate 1 passes, spawn Gates 2 + 3 + 4 + docs-sync-check as parallel agents (not sequential make calls)
- Start docs-sync-check background check BEFORE Gate 1, not after (it reads files, doesn't depend on test results)
- /zie-retro: launch ADR-write agent and ROADMAP-update agent simultaneously (already designed as parallel, fix execution to match)
- Update both to use general-purpose agent type (not zie-framework:retro-format which may not be available in all sessions)

**Out of Scope:**
- Changing gate logic or pass/fail conditions
- Unit + integration parallelism (share test environment — can't safely parallelize)
