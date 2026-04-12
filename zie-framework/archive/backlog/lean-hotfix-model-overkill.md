# Backlog: Fix /hotfix model — opus is overkill for emergency minimal track

**Problem:**
/hotfix uses `model: claude-opus-4-6` for a 5-step minimal emergency fix workflow.
/fix (the fuller bug fix with regression test + verify skill) uses sonnet.
The assignment is inverted: the simpler, faster emergency track costs more than
the thorough one.

**Motivation:**
hotfix is described as "minimal fix, cannot wait for full pipeline" — 5 steps,
54 lines, goes straight to commit+release. opus-4-6 is the most expensive model
in the stack. Sonnet (or haiku) is sufficient for this track. Direct cost reduction
on every /hotfix invocation.

**Rough scope:**
- Change `model: claude-opus-4-6` → `model: claude-sonnet-4-6` in commands/hotfix.md
- Change `effort: high` → `effort: low` (5-step mechanical track, no extended thinking needed)
- Verify no hotfix-specific reasoning is needed that requires opus
- Tests: frontmatter lint check (if exists)
