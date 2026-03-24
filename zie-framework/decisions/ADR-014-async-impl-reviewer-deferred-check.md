# ADR-014: Async impl-reviewer with Deferred-Check Polling Pattern

Date: 2026-03-24
Status: Accepted

## Context

`/zie-implement` runs impl-reviewer after each task's REFACTOR phase. The synchronous
approach (block until reviewer returns) stalls implementation momentum — the reviewer
reads files, loads ADRs, and runs its checklist while Claude sits idle. For a plan
with 8 tasks, this adds 8 sequential reviewer wait times to the total session length.
The alternative of no reviewer at all removes the quality gate.

## Decision

Spawn `@agent-impl-reviewer` asynchronously (`background: true`) immediately after
REFACTOR completes. The caller does not block — it records a `{ task_id, reviewer_handle,
reviewer_status: pending }` entry in a `pending-reviewers` list and announces the
next task immediately.

At the **start of each task loop iteration**, poll every pending-reviewer handle:

- `pending` → still running; continue current task, check again next iteration
- `approved` → clear entry, no action needed
- `issues_found` → halt current task, surface feedback, apply fixes, re-run tests,
  re-invoke reviewer synchronously (blocking). Max 3 total iterations; background
  spawn counts as iteration 1.

Before the final commit, wait for all remaining pending reviewers (timeout: 120s).

## Consequences

**Positive:** Reviewer work runs in parallel with the next task. For multi-task
plans, total wall-clock time decreases significantly. Issues are surfaced at the
next task boundary rather than immediately — usually sufficient, since the next task
typically touches different files.

**Negative:** A reviewer returning `issues_found` may interrupt a partially started
subsequent task, requiring context switching. The pending-reviewers list adds state
management complexity to the task loop. The 120s final-wait can stall a commit if
a reviewer hangs.

**Neutral:** The background spawn counts as iteration 1 toward the 3-iteration max,
preserving the same quality gate depth as synchronous review.

## Amendment

Amended by `reviewer-fail-fast` (2026-03-24): iteration cap reduced from 3 to 2
(initial scan + confirm pass) for `impl-reviewer` in `zie-implement.md`.

The background spawn remains pass 1 (initial scan). If `issues_found`, a single
synchronous confirm pass (pass 2) is invoked after fixes are applied. There is no
third iteration — persistent issues after the confirm pass are surfaced directly to
Zie. This replaces the previous "Max 3 total iterations" note in the Decision section.
