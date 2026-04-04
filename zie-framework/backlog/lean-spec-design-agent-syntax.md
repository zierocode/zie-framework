# Backlog: Fix spec-design @agent-spec-reviewer → Skill() invocation

**Problem:**
spec-design/SKILL.md Step 5 dispatches `@agent-spec-reviewer` which is not a
documented Claude Code invocation pattern. The canonical mechanism is `Skill()`.
A fallback comment says `<!-- fallback: Skill(zie-framework:spec-reviewer) -->`,
suggesting the author was uncertain. All other commands use `Skill(zie-framework:...)`
consistently. This creates a reliability gap specifically in the spec-review loop.

**Motivation:**
If `@agent-spec-reviewer` doesn't resolve, the spec-reviewer is silently skipped —
no error, no fallback triggered, spec quality gate bypassed. This is the most critical
quality gate in the pipeline (spec correctness blocks all downstream work).

**Rough scope:**
- Replace `@agent-spec-reviewer` with `Skill(zie-framework:spec-reviewer)` in
  spec-design/SKILL.md Step 5
- Remove the fallback comment (no longer needed)
- Verify the same pattern is consistent in write-plan, debug, verify skills
- Tests: structural test asserting no `@agent-` syntax in any skill file
