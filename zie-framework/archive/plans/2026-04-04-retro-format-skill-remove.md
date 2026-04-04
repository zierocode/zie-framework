---
slug: retro-format-skill-remove
spec: zie-framework/specs/2026-04-04-retro-format-skill-remove-design.md
created: 2026-04-04
---

# Plan: Remove Deprecated retro-format Skill

## Pre-flight

- [ ] Run `make test-ci` — confirm baseline passes

## Steps

### 1. Delete skill directory

```bash
rm -rf /Users/zie/Code/zie-framework/skills/retro-format
```

### 2. Delete test_retro_format_skill.py (entire file)

File: `tests/unit/test_retro_format_skill.py`
Action: delete entirely — all 3 tests validate the now-deleted SKILL.md.

### 3. Update test_skill_pruning.py — remove TestRetroFormatPruning class

File: `tests/unit/test_skill_pruning.py`
Action: delete the entire `TestRetroFormatPruning` class (lines ~267–316, 9 test methods).

### 4. Update test_skills_advanced_features.py — remove "retro-format" from NO_ARG_SKILLS

File: `tests/unit/test_skills_advanced_features.py`
Action: remove `"retro-format",` from the `NO_ARG_SKILLS` list in `TestArgumentHintFrontmatter`.

### 5. Update test_skills_frontmatter.py — remove retro-format entries

File: `tests/unit/test_skills_frontmatter.py`
Actions:
- Delete `test_retro_format_user_invocable_false` test method (~lines 60–63)
- Remove `"retro-format",` from the `ALL_SKILLS` list (~line 91)

### 6. Update test_model_effort_frontmatter.py — remove retro-format entries

File: `tests/unit/test_model_effort_frontmatter.py`
Actions:
- Remove `"skills/retro-format/SKILL.md": ("haiku", "low"),` from `EXPECTED` dict (~line 39)
- Remove `"skills/retro-format/SKILL.md",` from `EXPECTED_HAIKU` list (~line 159)

### 7. Update test_retro_general_purpose_agent.py — remove fallback assertion

File: `tests/unit/test_retro_general_purpose_agent.py`
Action: delete `test_retro_format_fallback_via_skill` method (~lines 31–35).
Rationale: that test asserts `"retro-format" in zie-retro.md` as a fallback comment — once
the skill is gone, that comment reference should also be removed from the command and the
test deleted. If the prose label in `zie-retro.md` is kept, delete only the test; if the
label is also cleaned up, both go together.

> Note: check `commands/zie-retro.md` line 43 (`Build compact JSON bundle for retro-format fork:`)
> — if it's safe to rename to a generic label (e.g., `Build compact JSON bundle:`), do so
> and then delete the test. If renaming would break other tests, delete only the test.

### 8. Verify

- [ ] `make test-ci` — zero failures
- [ ] `Glob("skills/*/SKILL.md")` — no retro-format entry

## Rollback

No rollback needed — git history preserves the deleted files.
