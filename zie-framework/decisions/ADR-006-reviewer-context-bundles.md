# ADR-006: Reviewer Context Bundles (Phase 1/2/3 Structure)

Date: 2026-03-23
Status: Accepted

## Context

The three reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer)
previously reviewed documents in isolation — they read only the submitted
spec/plan/changed files without cross-referencing the actual codebase,
ADR history, or active ROADMAP. This meant reviewers couldn't catch
file-existence errors, ADR conflicts, or duplicate scope with in-progress
features.

## Decision

Restructure all three reviewer skills into three phases:

- **Phase 1 — Load Context Bundle**: before reviewing, load named
  component files, all `decisions/*.md` ADRs, `project/context.md`,
  and ROADMAP (Now + Ready + Next lanes only). Skip gracefully if any
  source is missing — never block review.
- **Phase 2 — Review Checklist**: the existing per-skill review criteria
  (unchanged, just renumbered to Phase 2).
- **Phase 3 — Context Checks**: cross-reference the document against
  the loaded bundle. Checks: file existence (flag missing files not
  marked Create), ADR conflict (flag decisions that contradict loaded
  ADRs), ROADMAP conflict (flag duplicate scope with Ready/Now items),
  pattern match (flag divergence from observed patterns — surfaces for
  human decision, reviewer does not decide).

`impl-reviewer` omits the ROADMAP conflict check (implementation is
already approved; scope conflict is a spec/plan concern).

## Consequences

- Reviewers now catch real-world issues: missing files, ADR violations,
  duplicate feature scope.
- The graceful-skip rule means a missing decisions/ or ROADMAP never
  blocks review.
- Phase numbering in the skill files restarts at 1 per phase (not
  continuing across phases) to satisfy markdownlint MD029.
- The context bundle adds latency to each review invocation (file reads
  before checklist) — acceptable for the quality improvement.
