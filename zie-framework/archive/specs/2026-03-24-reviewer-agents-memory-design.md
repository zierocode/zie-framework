---
approved: true
approved_at: 2026-03-24
backlog: backlog/reviewer-agents-memory.md
---

# Reviewer Skills → Custom Agents with Persistent Memory — Design Spec

**Problem:** The three reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) run inline as skills — they consume main-conversation context, run on full Sonnet, and have no cross-session memory, so review quality cannot improve over time.

**Approach:** Convert each reviewer into a Claude Code custom agent file (`agents/<name>.md`) with `model: haiku`, `permissionMode: plan`, and `memory: project`. Agents run in isolated context (no main-conversation pollution), accumulate review patterns across sessions via `.claude/agent-memory/<agent-name>/`, and are 3-5x cheaper than Sonnet for structured checklist tasks. The existing skill files are kept intact as fallback; commands swap `Skill(zie-framework:<reviewer>)` for `@agent-<reviewer>` syntax.

**Components:**
- Create: `agents/spec-reviewer.md` — agent frontmatter + embedded system prompt (Phase 1-3 review logic from `skills/spec-reviewer/SKILL.md`)
- Create: `agents/plan-reviewer.md` — agent frontmatter + embedded system prompt (Phase 1-3 review logic from `skills/plan-reviewer/SKILL.md`)
- Create: `agents/impl-reviewer.md` — agent frontmatter + embedded system prompt (Phase 1-3 review logic from `skills/impl-reviewer/SKILL.md`); adds `Bash(make test*)` to allowed tools
- Modify: `skills/spec-design/SKILL.md` — replace `Skill(zie-framework:spec-reviewer)` with `@agent-spec-reviewer`
- Modify: `commands/zie-plan.md` — replace `Skill(zie-framework:plan-reviewer)` with `@agent-plan-reviewer`
- Modify: `commands/zie-implement.md` — replace `Skill(zie-framework:impl-reviewer)` with `@agent-impl-reviewer`
- Modify: `zie-framework/project/components.md` — add Agents section to registry

**Data Flow:**

1. Caller (skill or command) finishes drafting artifact (spec / plan / implementation).
2. Caller invokes `@agent-<reviewer>` passing: artifact path + relevant context (backlog context, spec path, or files-changed list).
3. Claude Code spawns the agent in isolated context; agent loads `memory: project` from `.claude/agent-memory/<agent-name>/` — accumulated review patterns from prior sessions are available.
4. Agent executes Phase 1 (load context bundle via Read/Grep/Glob), Phase 2 (checklist evaluation), Phase 3 (cross-reference checks).
5. Agent writes any new review patterns / learned heuristics back to its memory store on completion.
6. Agent returns structured verdict (`APPROVED` or `Issues Found`) to caller.
7. Caller applies existing retry logic (max 3 iterations → surface to human) — no change to retry behavior.

**Edge Cases:**
- **Agent not found** — if `@agent-<reviewer>` resolution fails (e.g., agent file missing or Claude Code version doesn't support agents dir), caller falls back to `Skill(zie-framework:<reviewer>)`. Fallback is explicit in each modified command/skill via an inline comment.
- **Memory dir missing** — `.claude/agent-memory/<agent-name>/` does not exist on first run. Agent runtime creates it automatically; no pre-creation needed in agent file.
- **Haiku unavailable** — if `model: haiku` cannot be resolved (org policy or API error), Claude Code inherits the session model. No special handling needed in agent file; runtime falls back silently.
- **Agent invoked with insufficient context** — caller passes empty `files-changed` list or missing spec path. Agent Phase 1 handles gracefully: "FILE NOT FOUND" noted, review continues with available context (matches existing skill behavior).
- **Memory pollution across projects** — memory scope is `project`, so `.claude/agent-memory/` is per-project root. No cross-project bleed.

**Out of Scope:**
- Removing the skill versions (`skills/spec-reviewer/`, `skills/plan-reviewer/`, `skills/impl-reviewer/`) — kept as permanent fallback.
- Changing reviewer logic, checklist items, or output format — agent system prompts mirror the existing SKILL.md content verbatim.
- Exposing reviewers as user-invocable commands — all three are `user-invocable: false`; invocation is always via caller skill/command.
- Migrating other skills (tdd-loop, debug, verify, etc.) to agents — out of scope for this feature.
- Implementing memory summarization or eviction policy — default Claude Code memory behavior applies.
- Adding reviewer telemetry or structured memory schema — plain natural-language memory entries, same as other agents.
