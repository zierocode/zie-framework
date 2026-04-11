# Fix spec-design @agent-spec-reviewer → Skill() Invocation — Design Spec

**Problem:** `skills/spec-design/SKILL.md` Step 5 dispatches `@agent-spec-reviewer`, which is not the correct invocation pattern for skills. Skills must call `Skill(zie-framework:spec-reviewer)` directly; `@agent-` syntax is reserved for commands that spawn isolated subagent worktrees. The fallback comment `<!-- fallback: Skill(zie-framework:spec-reviewer) -->` is never triggered, leaving the spec-reviewer quality gate silently bypassable.

**Approach:** Replace `@agent-spec-reviewer` with `Skill(zie-framework:spec-reviewer)` directly in spec-design/SKILL.md Step 5, remove the now-redundant fallback comment, and add a structural pytest guard that asserts no SKILL.md file contains `@agent-` syntax.

**Components:**
- Modify: `skills/spec-design/SKILL.md` — replace `@agent-spec-reviewer` dispatch with `Skill(zie-framework:spec-reviewer)` invocation; remove fallback HTML comment
- Create: `tests/unit/test_skill_agent_syntax.py` — structural test asserting no `skills/*/SKILL.md` file contains `@agent-` syntax

**Data Flow:**
1. User invokes `/spec lean-spec-design-agent-syntax` → spec-design skill runs
2. Step 5 of spec-design calls `Skill(zie-framework:spec-reviewer)` directly (no subagent spawn, no worktree isolation)
3. spec-reviewer runs inline, returns ✅ APPROVED or ❌ Issues Found
4. spec-design loops on Issues Found (up to 3 iterations) as before
5. On APPROVED, spec-design writes frontmatter and prints handoff — unchanged

**Edge Cases:**
- `@agent-` syntax in archived plans/specs — these are historical documents; the test must scope to `skills/*/SKILL.md` only (not `zie-framework/archive/`)
- `@agent-plan-reviewer` in `commands/plan.md` and `@agent-impl-reviewer` in `commands/implement.md` — these are commands, not skills; `@agent-` IS correct there and must not be flagged
- Fallback comment removal — existing tests (test_spec_design_batch_approval.py) only assert `"spec-reviewer" in text`, not the HTML comment; safe to remove
- The `@agent-spec-reviewer` literal appears in archive files and test assertions from the reviewer-agents-memory plan — the new structural test must not match those paths

**Out of Scope:**
- Changing `@agent-plan-reviewer` in `commands/plan.md` (commands are a different execution context; `@agent-` is valid there)
- Changing `@agent-impl-reviewer` in `commands/implement.md` (same reason)
- Modifying agents/spec-reviewer.md (the agent definition file is correct as-is)
- Adding worktree isolation to the Skill() invocation path (not needed — skills run inline)
- Any changes to write-plan, debug, or verify skills (they do not contain `@agent-` syntax)
