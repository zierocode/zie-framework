# Remove Deprecated retro-format Skill

## Problem

`skills/retro-format/SKILL.md` is marked `deprecated: true` and is never invoked (retro format was inlined into `zie-retro` command). However it remains discoverable via `Glob("skills/*/SKILL.md")` and adds ~140 lines of context overhead to any skills scan, including docs-sync checks.

## Motivation

Dead skill file adds token overhead on every skills directory scan. If the retro format logic is needed as reference, it's already in the retro command and in git history. The deprecated file should be removed to keep the skills directory containing only active skills.

## Rough Scope

- Delete `skills/retro-format/SKILL.md` and the `skills/retro-format/` directory
- Verify no command or skill references it by name
- Update any test that counts skills or globs the skills directory
