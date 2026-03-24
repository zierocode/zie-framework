# Backlog: Skills context:fork — Run Reviewer Skills as Isolated Subagents

**Problem:**
Reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) run inline in the
main conversation. Their verbose output fills the main context window. A spec
review that reads 20 files pollutes the conversation with all those Read calls.

**Motivation:**
Skills support `context: fork` + `agent:` frontmatter to run in an isolated
subagent context. The subagent does all the heavy lifting (file reads, analysis)
and returns only the structured verdict to the main conversation. This is the
correct pattern for any skill that reads many files without needing conversation
history.

**Rough scope:**
- Add `context: fork` + `agent: Explore` to spec-reviewer, plan-reviewer
- Add `context: fork` + `agent: general-purpose` to impl-reviewer (needs Bash
  for make test-unit)
- Add `allowed-tools:` per skill to restrict what the forked agent can use
- Test that APPROVED / Issues Found verdict still surfaces to main conversation
- Note: `context: fork` skills don't see main conversation history — reviewers
  must be self-contained (already are, via their Phase 1 context load)
- Tests: skill still returns structured verdict, no context leak
