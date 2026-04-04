# Consolidate docs-sync-check to Single Skill Invocation

## Problem

The docs-sync check exists in 3 forms: (1) inline Markdown prose in `commands/zie-retro.md` (lines 66-81), (2) a dedicated `skills/docs-sync-check/SKILL.md`, and (3) an inline Bash one-liner in `commands/zie-release.md`. All three check different subsets of the same thing (commands, skills, hooks vs CLAUDE.md/README). Divergence between them is already present — the release Bash check doesn't verify hooks.

## Motivation

Three implementations mean three maintenance points and guaranteed behavioral drift. Consolidating to a single `Skill(zie-framework:docs-sync-check)` call in both `zie-retro` and `zie-release` eliminates ~16 lines of inline prose from `zie-retro`, ensures consistency, and makes the skill the single authoritative source for what "docs in sync" means.

## Rough Scope

- Replace inline docs-sync block in `commands/zie-retro.md` with `Skill(zie-framework:docs-sync-check)`
- Replace Bash one-liner in `commands/zie-release.md` with `Skill(zie-framework:docs-sync-check)`
- Verify `skills/docs-sync-check/SKILL.md` covers all three check types (commands, skills, hooks)
