---
approved: true
approved_at: 2026-04-04
backlog: backlog/model-fix-effort-medium-to-low.md
---

# Drop /fix Effort medium → low — Design Spec

**Problem:** `commands/fix.md` uses `model: sonnet` + `effort: medium` (extended thinking). `/fix` follows a systematic debug checklist — reproduce, isolate, identify root cause, fix, write regression test, verify — which is sequential structured work. Extended thinking does not improve ordered protocol execution and adds unnecessary token cost on every bug-fix invocation.

**Approach:** Change `effort: medium` to `effort: low` in `commands/fix.md` frontmatter. No logic or step changes — the checklist remains identical. Update `tests/unit/test_model_effort_frontmatter.py` EXPECTED map so CI enforces the new value and catches any future regression back to medium.

**Components:**
- `commands/fix.md` — change `effort: medium` → `effort: low` in frontmatter
- `tests/unit/test_model_effort_frontmatter.py` — update `"commands/fix.md"` entry in `EXPECTED` from `("sonnet", "medium")` to `("sonnet", "low")`

**Data Flow:**
1. User invokes `/fix` (or Claude Code routes a bug intent to `/fix`)
2. Claude Code reads `commands/fix.md` frontmatter; sets `effort: low` — no extended thinking budget allocated
3. `/fix` proceeds through its checklist: reproduce → isolate → root cause → regression test (RED) → fix (GREEN) → verify
4. `Skill(zie-framework:debug)` is invoked for the reproduce/isolate steps (debug skill already at `effort: low` after its own downgrade)
5. Fix completes and is committed; tokens saved vs. prior `medium` budget on every invocation

**Edge Cases:**
- `test_model_effort_frontmatter.py` currently has `"commands/fix.md": ("sonnet", "medium")` — must be updated to `("sonnet", "low")` or `TestExpectedValues::test_correct_effort_values` will fail in CI
- `effort: low` is consistent with other structured-checklist commands (e.g. `commands/status.md`, `commands/backlog.md`) and reviewer skills that also run checklists at low effort
- The debug sub-skill (`skills/debug/SKILL.md`) is already `effort: low` — this change aligns the calling command with its sub-skill

**Out of Scope:**
- Changing the model (stays `sonnet`)
- Modifying `/fix` checklist steps or logic
- Changing the `debug` skill (already downgraded)
- Applying this pattern to any other command not identified in this spec
- Performance benchmarking or A/B testing of fix quality at low vs. medium
