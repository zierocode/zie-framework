# Consolidate Reviewer Skills Phase 1 Context-Load Boilerplate

## Problem

All three reviewer skills (`spec-reviewer/SKILL.md`, `plan-reviewer/SKILL.md`, `impl-reviewer/SKILL.md`) contain an identical 30-line "Phase 1 — Load Context Bundle" block: check for `context_bundle`, fall back to disk, call `get_cached_adrs`, read `project/context.md`, read ROADMAP.md. Each file pays the full token cost of this boilerplate at runtime inside its subagent context window.

## Motivation

30 lines × 3 files = 90 lines of identical prose that must be kept synchronized. Any change to the caching protocol requires 3 edits. Extracting to a shared include or preamble pattern eliminates both the maintenance burden and the token overhead per reviewer invocation.

## Rough Scope

- Extract Phase 1 context-load block into a shared skill (e.g. `skills/reviewer-context/SKILL.md`) or reference pattern
- Replace the 3 inline copies with a pointer/include reference
- Verify all three reviewers still receive the required context bundle
- Update tests for reviewer skills
