---
slug: retro-format-skill-remove
created: 2026-04-04
status: approved
---

# Spec: Remove Deprecated retro-format Skill

## Problem

`skills/retro-format/SKILL.md` is marked `deprecated: true` since 2026-04-04 and is never
invoked — retro format logic is inlined in `zie-retro.md`. The directory persists as dead
weight, adding ~140 lines of context overhead to every skills directory scan.

## Goal

Delete `skills/retro-format/` and remove all test coverage that validates the now-gone file.

## Scope

**In scope:**
- Delete `skills/retro-format/SKILL.md` and parent directory
- Delete `tests/unit/test_retro_format_skill.py` (entire file validates deleted skill)
- Update `tests/unit/test_skill_pruning.py` — remove `TestRetroFormatPruning` class
- Update `tests/unit/test_skills_advanced_features.py` — remove `"retro-format"` from `NO_ARG_SKILLS` list
- Update `tests/unit/test_skills_frontmatter.py` — remove `test_retro_format_user_invocable_false` test and `"retro-format"` from `ALL_SKILLS` list
- Update `tests/unit/test_model_effort_frontmatter.py` — remove `"skills/retro-format/SKILL.md"` from `EXPECTED` dict and `EXPECTED_HAIKU` list
- Update `tests/unit/test_retro_general_purpose_agent.py` — remove `test_retro_format_fallback_via_skill` (asserts `"retro-format" in text` for zie-retro.md)

**Out of scope:**
- `commands/zie-retro.md` — the one reference (`Build compact JSON bundle for retro-format fork:`) is a prose label in a code comment, not an invocation; leave as-is

## Acceptance Criteria

1. `skills/retro-format/` directory does not exist
2. `make test-ci` passes with zero failures
3. No test references `read_skill("retro-format")` or `SKILL_PATH` pointing to retro-format
4. `Glob("skills/*/SKILL.md")` returns no retro-format entry
