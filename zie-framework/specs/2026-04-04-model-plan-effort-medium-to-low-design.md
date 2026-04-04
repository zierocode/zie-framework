# Drop /plan Effort medium → low — Design Spec

**Problem:** `commands/plan.md` sets `effort: medium` on its frontmatter, but /plan is a thin orchestrator — it validates a spec exists, invokes `Skill(write-plan)`, invokes `Skill(plan-reviewer)`, and writes the plan file. All reasoning work happens inside `write-plan` (sonnet+medium). The command's main thread does coordination, not deep reasoning, so `effort: medium` is wasteful.

**Approach:** Change the single `effort: medium` → `effort: low` in `commands/plan.md` frontmatter. No logic changes are needed. `write-plan` skill retains `model: sonnet` + `effort: medium` because that is where planning quality matters. The test `test_model_effort_frontmatter.py` must be updated to assert `effort: low` for `commands/plan.md` to match the new expectation.

**Components:**
- `commands/plan.md` — frontmatter `effort: medium` → `effort: low`
- `tests/test_model_effort_frontmatter.py` — update expected effort for `plan.md`

**Data Flow:**
1. User runs `/plan <slug>`.
2. Claude Code reads `commands/plan.md` frontmatter → allocates `effort: low` for orchestration thread.
3. Orchestrator validates spec, invokes `Skill(zie-framework:write-plan)` (sonnet+medium — unchanged).
4. `write-plan` produces the plan; orchestrator invokes `Skill(zie-framework:plan-reviewer)`.
5. Reviewer approves; orchestrator writes frontmatter + moves item in ROADMAP.

**Edge Cases:**
- Test suite asserts `effort: medium` for `plan.md` → must update to `effort: low` to avoid red CI.
- `write-plan` and `plan-reviewer` skills are not touched — only the command frontmatter changes.
- No `.config` key or runtime flag guards this change; it is unconditional.

**Out of Scope:**
- Changing `write-plan` or `plan-reviewer` effort levels.
- Any changes to spec, implement, or release commands.
- Adding a config toggle for per-command effort overrides.
