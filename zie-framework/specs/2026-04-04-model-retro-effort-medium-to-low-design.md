---
approved: true
approved_at: 2026-04-04
backlog: backlog/model-retro-effort-medium-to-low.md
---

# Drop /retro effort: medium → low — Design Spec

**Problem:** `/retro` uses `effort: medium` on `sonnet`, but retro is purely structured slot-filling (git log → ADR template → ROADMAP Done → docs-sync-check). No step requires extended reasoning; the output is template-driven and deterministic from inputs.

**Approach:** Change `effort: medium` → `effort: low` in `commands/retro.md` frontmatter, and update the `EXPECTED` map in `tests/unit/test_model_effort_frontmatter.py` to assert the new value. The test is the single enforcement gate — changing the file without updating the test fails CI immediately, so both changes ship together.

**Components:**
- `commands/retro.md` — frontmatter `effort: medium` → `effort: low`
- `tests/unit/test_model_effort_frontmatter.py` — `EXPECTED["commands/retro.md"]` tuple `("sonnet", "medium")` → `("sonnet", "low")`

**Data Flow:**
1. User invokes `/retro`
2. Claude Code reads `commands/retro.md` frontmatter → sets `model: sonnet`, `effort: low`
3. Retro executes: git log read → ADR slot-fill → ROADMAP Done update → docs-sync-check
4. All steps are deterministic template operations; low effort is sufficient

**Edge Cases:**
- No runtime behavior change — effort is a model hint only; retro output quality is unchanged
- Test enforcement: `TestExpectedValues.test_correct_effort_values` catches any mismatch between file and EXPECTED map
- ADR-022 precedent: `write-plan` downgraded `high` → `medium` for same reason (template-driven output); this applies identical logic one tier lower

**Out of Scope:**
- Changing `model: sonnet` (retro still benefits from sonnet's instruction-following for template fills)
- Downgrading effort on any other command or skill (separate backlog items)
- Changes to retro logic, steps, or output format
