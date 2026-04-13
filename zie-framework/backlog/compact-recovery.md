# compact-recovery

## Problem

When Claude Code compacts conversation context (either automatically or via `/compact`), the workflow often stalls or loses track. The `sdlc-compact.py` hook saves a snapshot to `/tmp` and restores it via `additionalContext`, but: (a) `/tmp` snapshots don't survive machine restarts, (b) multi-level compaction overwrites previous snapshots, (c) the restored context is a text summary only — it cannot restore tool-call history or file-edit state, (d) the sprint command forces `/compact` between Phase 2 items but the `.sprint-state` file only tracks which items are done, not what the current task state is within an item, (e) there's no mechanism to verify the workflow is still active after a compact.

## Motivation

Context compaction is the #1 cause of workflow stalls. Users report that after a compact, the model "forgets" where it was and either stops working or starts a different task. This is especially painful during long `/implement` sessions.

## Rough Scope

1. **Compact verification in session-resume** — After `PostCompact` fires, `session-resume.py` should check if a workflow is active (read `.sprint-state` or ROADMAP Now lane) and inject a continuation hint: "Sprint Phase 2 in progress — continue with item X."
2. **Sprint state enrichment** — Extend `.sprint-state` JSON to include `current_task`, `tdd_phase`, and `last_action` fields. Update these after each significant step so compact recovery has more context than just "which items are done."
3. **PostCompact active-workflow guard** — In `sdlc-compact.py` PostCompact handler, if `.sprint-state` exists, inject a mandatory continuation directive in `additionalContext` that tells the model to continue the sprint (not start a new task).
4. **Simplify compact-hint thresholds** — The current 3-tier system (70/80/90%) is over-engineered for most sessions. Consolidate to 2 tiers: 75% (advisory) and 90% (mandatory compact suggestion).