## ADR-022: Effort Routing Strategy for Skills and Commands

**Date:** 2026-03-27
**Status:** Accepted (Compressed from ADR-000-summary.md)

## Context

Skills and commands were inconsistently using `effort: high` even for simple
checklist and review tasks. `write-plan` was marked `high` despite being a
medium-complexity task. Over-specifying effort wastes tokens and increases
latency unnecessarily.

## Decision

Reserve `effort: high` for `spec-design` only (brainstorming + design work
that benefits from deeper reasoning). All other skills default to `medium` or
`low`. Specifically, `write-plan` corrected from `high` → `medium`.

## Consequences

- Reduced token cost for plan writing and review tasks.
- `spec-design` retains high effort for quality ideation.
- Enforced by test (`test_model_effort_frontmatter.py`).
