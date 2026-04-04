# Drop write-plan Effort: medium → low — Design Spec

**Problem:** `skills/write-plan/SKILL.md` uses `effort: medium` despite producing structured, schema-driven output (task list with file assignments, depends_on, test coverage). Extended thinking time does not improve plan quality for well-specified inputs — plan quality correlates with upstream spec quality and skill instructions, not reasoning budget.

**Approach:** Change the single `effort: medium` field to `effort: low` in `skills/write-plan/SKILL.md` frontmatter. Update `EXPECTED` map in `tests/unit/test_model_effort_frontmatter.py` to assert `("sonnet", "low")` for this path. No logic changes — purely a configuration + test update.

**Components:**
- `skills/write-plan/SKILL.md` — frontmatter field change (`effort: medium` → `effort: low`)
- `tests/unit/test_model_effort_frontmatter.py` — update `EXPECTED["skills/write-plan/SKILL.md"]` tuple from `("sonnet", "medium")` to `("sonnet", "low")`

**Data Flow:**
1. Claude Code reads `skills/write-plan/SKILL.md` frontmatter when invoking the `write-plan` skill
2. `effort: low` is passed to the model runtime — no extended thinking budget allocated
3. Skill executes identically to before; only reasoning budget is reduced
4. `test_model_effort_frontmatter.py` `TestExpectedValues.test_correct_effort_values` verifies the new value

**Edge Cases:**
- ADR-022 documents write-plan as corrected `high → medium`; this change extends that correction to `medium → low`. ADR-022 is not superseded — the reasoning still holds, and this change is consistent with its principle (avoid over-specifying effort for structured tasks).
- No other skill or command references write-plan's effort level.
- `test_model_effort_frontmatter.py` line for `"skills/write-plan/SKILL.md"` must be updated atomically with the SKILL.md change or tests will break.

**Out of Scope:**
- Changing the model (remains `sonnet`)
- Effort changes to any other skill or command
- Changes to write-plan skill logic or output format
- ADR update (change is a continuation of ADR-022 intent, not a new architectural decision)
