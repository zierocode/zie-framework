# Spec: Remove Duplicate Reviewer Loop from write-plan Skill
status: draft

## Problem

`skills/write-plan/SKILL.md` ends with a "invoke plan-reviewer, repeat until APPROVED" loop. `commands/zie-plan.md` has an identical reviewer gate that runs after calling the write-plan skill. Every plan cycle therefore runs the plan-reviewer at least twice (inner skill loop + outer command loop), and up to 4 times when both loops trigger a revision pass. Each reviewer invocation may spawn a subagent.

The skill's single responsibility is to produce the plan file. Gating (review + approve) belongs to the orchestrating command, not the skill.

## Solution

Remove the reviewer loop block from `skills/write-plan/SKILL.md` (the "After saving, run the plan reviewer loop" section and all instructions beneath it, up to the ROADMAP update instruction). The skill ends after saving the plan file.

The ROADMAP update instruction in `write-plan/SKILL.md` ("Then update zie-framework/ROADMAP.md") is also redundant — `zie-plan.md` handles ROADMAP updates atomically after reviewer approval. Remove it too.

Update two unit tests that assert `plan-reviewer` is referenced inside `write-plan/SKILL.md` — flip them to assert the reviewer is referenced in `zie-plan.md` (which is already true) and that it is NOT inside the skill.

## Acceptance Criteria

- [ ] `skills/write-plan/SKILL.md` no longer contains a plan-reviewer invocation block or ROADMAP update instruction
- [ ] `commands/zie-plan.md` plan-reviewer gate is unchanged and remains the authoritative reviewer loop
- [ ] `tests/unit/test_sdlc_pipeline.py::test_write_plan_invokes_plan_reviewer` is updated to assert that `zie-plan.md` contains `plan-reviewer` (not the skill)
- [ ] `tests/unit/test_skills_advanced_features.py::test_write_plan_documents_plan_reviewer` is updated to assert the skill does NOT invoke the reviewer (ownership moved to command)
- [ ] `make test-ci` passes with no failures

## Out of Scope

- Changes to any other skill or command
- Changes to `commands/zie-plan.md` reviewer logic
- Changes to `skills/plan-reviewer/SKILL.md`
- Any Python hook changes
