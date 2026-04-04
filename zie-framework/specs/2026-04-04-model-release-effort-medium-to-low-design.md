# Drop /release effort medium → low — Design Spec

**Problem:** `/release` uses `model: haiku` + `effort: medium`, but haiku gains negligible benefit from an extended token budget — the model's capability ceiling is the binding constraint, not effort. Medium effort wastes tokens for no quality gain on a command that is purely a checklist executor.

**Approach:** Change `effort: medium` → `effort: low` in the `commands/release.md` frontmatter. Update `test_model_effort_frontmatter.py` (the EXPECTED map and `TestHaikuFiles.EXPECTED_HAIKU` list) to assert `("haiku", "low")` for `commands/release.md`. No behavior change — the release checklist is deterministic and mechanical; effort does not alter its steps.

**Components:**
- `commands/release.md` — frontmatter `effort:` field
- `tests/unit/test_model_effort_frontmatter.py` — EXPECTED map + `TestHaikuFiles.EXPECTED_HAIKU`

**Data Flow:**
1. Claude Code reads `commands/release.md` frontmatter and selects `haiku` + `low` effort for the session.
2. The release checklist executes identically — no runtime logic depends on the effort value.
3. `test_model_effort_frontmatter.py` EXPECTED map asserts `("haiku", "low")` → test passes.
4. `TestHaikuFiles.EXPECTED_HAIKU` list includes `commands/release.md` → `test_haiku_files_have_low_effort` passes.

**Edge Cases:**
- `test_effort_audit.py` only scans `skills/*/SKILL.md` (not commands) — no change required.
- `test_skills_frontmatter.py` — verify it does not assert effort for `commands/release.md`; if it does, update accordingly.
- The two inline `<!-- model: sonnet reasoning: ... -->` comments inside the release command body are unaffected — they annotate specific reasoning steps, not the command-level model/effort frontmatter.

**Out of Scope:**
- Changing the model from haiku to another model.
- Altering any release gate logic or step ordering.
- Changing effort for any other command or skill.
- Adding a new ADR (this is a minor tuning consistent with ADR-022 policy, not a new decision).
