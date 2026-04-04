# ADR-055 — Sprint Phase 2 Collapse: Fold Plan Phase into Spec+Plan Parallel

**Status**: Accepted
**Date**: 2026-04-04
**Sprint**: sprint10-lean-quality-refactor-v1.19.0

## Context

The `/sprint` command had two sequential parallel phases:

- **Phase 1**: Spec all items in parallel (spec-design + spec-reviewer)
- **Phase 2**: Plan all items in parallel (write-plan + plan-reviewer)

For items entering the sprint from the **Next lane**, Phase 1 already ran the
full `spec → spec-review → write-plan → plan-review` chain. Phase 2 was
therefore redundant — these items arrived at Phase 2 already having approved
plans. Phase 2 was only meaningful for items in the **Ready lane** (already
specced, awaiting plan), but these items could also be handled by Phase 1 with
an inline check.

Having two distinct phases created an extra barrier, a second user confirmation
point, and additional ROADMAP re-reads between phases.

## Decision

Collapse Phase 2 into Phase 1 as an **inline retry**. Phase 1 now runs the
full `spec → review → plan → review` chain for each item, with a retry on
failure before halting. Items in the Ready lane that already have approved plans
skip the spec step and go straight to plan-review if needed.

Phase 2 as a named sprint phase is removed.

## Consequences

**Positive**
- Sprint execution: 5 phases → 4 phases (Spec+Plan → Impl → Release → Retro)
- One fewer ROADMAP re-read and user confirmation point
- Ready-lane items handled by Phase 1 logic, no separate orchestration needed

**Negative**
- Phase 2 provided an explicit checkpoint between spec approval and plan
  approval. Removing it means failures surface inside Phase 1 instead of at a
  clean boundary. Inline retry compensates but is less visible.

**Neutral**
- Plan-reviewer quality gate unchanged — still runs per plan, still blocks on
  failure; just lives inside Phase 1 now

## Alternatives

**Keep Phase 2, add skip logic for items with approved plans**: Considered but
rejected. Adding "skip if already planned" to Phase 2 essentially reimplements
Phase 1 with a different name. Simpler to collapse.
