---
approved: true
approved_at: 2026-04-04
backlog: zie-framework/backlog/model-debug-effort-medium-to-low.md
---

# Drop Debug Skill Effort medium → low — Design Spec

**Problem:** The debug skill uses `effort: medium` (extended thinking), but debugging is a sequential checklist — reproduce → isolate → fix → verify — where steps are explicit and ordered. Extended thinking doesn't improve structured protocol execution and costs tokens on every `/fix` invocation.

**Approach:** Change `effort: medium` to `effort: low` in `skills/debug/SKILL.md` frontmatter. No logic changes — the skill steps remain identical. Add or update the test assertion that enforces debug skill's effort value so CI catches any future regression back to medium.

**Components:**
- `skills/debug/SKILL.md` — change `effort: medium` → `effort: low`
- `tests/test_model_effort_frontmatter.py` — update or add assertion for debug skill effort = low

**Data Flow:**
1. `/fix` command invokes `Skill(zie-framework:debug)`
2. Claude Code reads `skills/debug/SKILL.md` frontmatter
3. `effort: low` is passed to the model at invocation time — no extended thinking budget allocated
4. Debug checklist executes identically: reproduce → isolate → fix → verify
5. Session ends; tokens saved vs. prior `medium` budget

**Edge Cases:**
- Test `test_model_effort_frontmatter.py` may currently assert `effort: medium` — must be updated to `low` or it will fail in CI
- `effort: low` is consistent with reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) which also run structured checklists at low effort

**Out of Scope:**
- Changing the debug skill steps or logic
- Changing the model (stays `sonnet`)
- Applying this change to any other skill not identified in this spec
- Performance benchmarking or A/B testing of debug quality at low vs. medium
