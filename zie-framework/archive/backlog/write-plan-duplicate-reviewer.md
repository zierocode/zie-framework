# Remove Duplicate Reviewer Loop from write-plan Skill

## Problem

`skills/write-plan/SKILL.md` ends with its own "invoke plan-reviewer, repeat until APPROVED" loop. `commands/zie-plan.md` has an identical reviewer gate that runs after calling the write-plan skill. This means every plan cycle runs 2 reviewer invocations minimum (inner skill loop + outer command loop), which can become 4 invocations if both loops require a revision pass. Each reviewer invocation may spawn a subagent.

## Motivation

The reviewer gate belongs in `zie-plan.md` (the orchestrating command), not inside the skill. The write-plan skill's job is to produce the plan file — not to gate it. Removing the loop from the skill eliminates 1-2 redundant subagent spawns per plan cycle and simplifies the skill's responsibility.

## Rough Scope

- Remove the reviewer loop block from `skills/write-plan/SKILL.md` (last ~10 lines)
- Verify `commands/zie-plan.md` reviewer gate still covers the full loop
- Update tests for write-plan skill if any assert the reviewer is invoked
