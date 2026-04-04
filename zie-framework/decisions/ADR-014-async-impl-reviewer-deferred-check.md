## ADR-014: Async impl-reviewer with Deferred-Check Polling Pattern

**Date:** 2026-03-24
**Status:** Accepted (Compressed from ADR-000-summary.md)

## Context

The impl-reviewer was previously synchronous — it blocked each REFACTOR phase
while waiting for a full review cycle. For large tasks with many REFACTOR
steps this significantly increased total implementation time.

## Decision

Spawn impl-reviewer async after each REFACTOR step using
`run_in_background=True`. Poll for completion at the start of the next task
iteration. Surface any issues found. Wait for all pending reviewers before the
final commit (iteration cap: 2 iterations per reviewer).

## Consequences

- Implementation speed improves since review runs in parallel with the next
  RED phase.
- Reviewer issues are surfaced at the start of the next task rather than
  blocking the current one.
- If a reviewer finds issues, the developer must address them before the
  subsequent REFACTOR can be marked complete.

## Amendment

**Date:** 2026-03-28
**Change:** Reviewer-fail-fast policy added. The iteration cap is enforced at
**2 total iterations** (initial + 1 re-review). If the reviewer still finds
issues after 2 iterations, the impl phase halts and surfaces the remaining
issues for human review rather than looping indefinitely.

The reviewer-fail-fast feature prevents runaway review loops that consume
unlimited tokens. After 2 iterations, escalate to the developer.
