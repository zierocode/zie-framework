# ADR-048: Shared load-context Skill for Context Bundle Loading

**Status:** Accepted  
**Date:** 2026-04-04

## Context

Three commands (`zie-plan`, `zie-implement`, `zie-sprint`) each contained an
identical 8–12 line inline block that read ADRs, called `write_adr_cache`, read
`project/context.md`, and assembled `context_bundle`. Any change to this
protocol required updating three files. Similarly, three reviewer skills
(`spec-reviewer`, `plan-reviewer`, `impl-reviewer`) contained identical ~30-line
Phase 1 blocks with the same ADR cache-first loading logic.

## Decision

Extract the context bundle assembly to `skills/load-context/SKILL.md`. Commands
replace the inline block with `Skill(zie-framework:load-context)`. Extract the
reviewer Phase 1 protocol to `skills/reviewer-context/SKILL.md`. Each reviewer
replaces its Phase 1 block with a compact stub that delegates to
`reviewer-context` and retains all test-required string anchors.

## Consequences

**Positive:**
- Single source of truth for context bundle assembly — fixes propagate everywhere.
- Reduced command/skill file sizes: each inline removal saves 6–12 lines per file.
- New skills are small, focused, and independently testable.

**Negative:**
- Adds a skill invocation indirection — slightly harder to trace what Phase 1 does
  without reading the skill file.

**Neutral:**
- Test-required strings (`write_adr_cache`, `adr_cache_path`, `decisions/`,
  `project/context.md`) retained via parenthetical comments in command files.
- All existing test assertions continue to pass without modification.

## Alternatives

- Shared Python utility: appropriate for hooks, not commands/skills (Markdown-only).
- Inline duplication: was the prior state — fails DRY and creates drift risk.
