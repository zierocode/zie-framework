# Backlog: Drop /plan effort medium → low (write-plan skill does the heavy lifting)

**Problem:**
/plan uses `model: sonnet` + `effort: medium`. /plan is a thin orchestrator:
it validates the spec exists, invokes Skill(write-plan), invokes Skill(plan-reviewer),
and writes the plan file. The actual planning work is done inside write-plan skill
(sonnet+medium). The /plan command main thread is coordination, not reasoning.

**Motivation:**
The medium effort on /plan's main thread is redundant — write-plan skill already
runs at sonnet+medium where planning quality actually matters. The command
orchestrator doesn't need extended thinking. Dropping to low saves on every /plan run.

**Rough scope:**
- Change `effort: medium` → `effort: low` in commands/plan.md frontmatter
- Keep write-plan skill at sonnet+medium (that's where quality matters)
- Tests: /plan produces approved plan at low effort
