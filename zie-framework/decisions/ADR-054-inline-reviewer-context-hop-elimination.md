# ADR-054 — Inline Reviewer Context: Eliminate Chain Hop

**Status**: Accepted
**Date**: 2026-04-04
**Sprint**: sprint10-lean-quality-refactor-v1.19.0

## Context

The spec-reviewer, plan-reviewer, and impl-reviewer skills each called
`Skill(zie-framework:reviewer-context)` as a separate hop to load ADR context
and project context. This added 3–4 chain depth per review cycle: caller →
reviewer → reviewer-context → disk reads → return. In a sprint with multiple
review loops, the cumulative hop overhead was measurable.

The `context_bundle` pass-through pattern (ADR-052) already provided a way to
pre-load context once and thread it through. Reviewers could be refactored to
accept inline context instead of delegating the load.

## Decision

Inline the context load directly in each reviewer skill. Remove the
`Skill(reviewer-context)` chain hop. Reviewers now read context directly when
no pre-loaded `context_bundle` is passed, rather than delegating to a
separate skill.

The `reviewer-context` skill remains available but is no longer in the default
reviewer chain.

## Consequences

**Positive**
- 3–4 hop chain → 1 hop per reviewer call
- Reviewers are self-contained — no hidden dependency on reviewer-context
- `context_bundle` pass-through still works for callers that pre-load (e.g. sprint)

**Negative**
- Slight text duplication across the three reviewer skills (each has the load
  logic inline rather than delegating)

**Neutral**
- reviewer-context skill exists but is no longer auto-invoked; can be called
  explicitly if a custom chain needs it

## Alternatives

**Keep reviewer-context as an intermediate hop**: Rejected. The abstraction
saved ~5 lines at the cost of 1 extra Skill() invocation per review. Net
negative for performance.
