# Spec: zie-sprint Phase 1 — Invoke Skills Directly Instead of Commands

- **slug**: sprint-phase1-skill-direct
- **status**: draft
- **date**: 2026-04-04

---

## Problem

Each Phase 1 parallel agent in `commands/zie-sprint.md` (lines 123–132) is
prompted to `Invoke /zie-spec <slug> --draft-plan`. This chains:

```
sprint-agent → /zie-spec command → spec-design skill → spec-reviewer skill
             → write-plan skill → plan-reviewer skill
```

That is 3 levels of nesting per item. For a 4-item sprint, up to 16 nested
skill invocations with repeated context serialization happen inside the command
control-plane wrapper — which itself adds no logic beyond sequencing skills.

## Solution

Rewrite the Phase 1 agent prompt block in `commands/zie-sprint.md` so each
parallel agent invokes the four skills directly in sequence:

1. `Skill(spec-design, "<slug> quick")` — write the spec
2. `Skill(spec-reviewer, "<slug>")` — review + approve spec
3. `Skill(write-plan, "<slug>")` — write the implementation plan
4. `Skill(plan-reviewer, "<slug>")` — review + approve plan

This removes the `/zie-spec` command wrapper from the critical path, reducing
nesting from 3 levels to 2 levels (sprint-agent → skill). Output is equivalent
because `/zie-spec --draft-plan` internally calls the same four skills in the
same order.

The Phase 2 comment referencing `--draft-plan` must also be updated to reflect
that plans are now produced in Phase 1 via the direct skill chain.

This is a **Markdown-only change** — no Python hooks, no test helpers, no new
files.

## Acceptance Criteria

1. `commands/zie-sprint.md` Phase 1 agent prompt no longer contains
   `/zie-spec` or `--draft-plan`.
2. Phase 1 agent prompt explicitly lists the four-skill sequence:
   `spec-design` → `spec-reviewer` → `write-plan` → `plan-reviewer`.
3. Each skill is invoked with the correct argument (`<slug>` or `<slug> quick`
   as appropriate).
4. Phase 1 agent prompt still instructs the agent to confirm both spec and plan
   are approved before returning.
5. Phase 2 comment (`--draft-plan` reference) is updated to accurately describe
   the new Phase 1 output.
6. `make lint` passes with no errors.
7. Existing sprint command tests (if any) continue to pass.

## Out of Scope

- Changes to `spec-design`, `spec-reviewer`, `write-plan`, or `plan-reviewer`
  skills themselves.
- Changes to `/zie-spec` command.
- Changes to Phase 2, Phase 3, or Phase 4 of `zie-sprint.md`.
- Performance benchmarking or timing comparisons.
- New test coverage for sprint Phase 1 (no test file exists today; adding tests
  is a separate backlog item).
