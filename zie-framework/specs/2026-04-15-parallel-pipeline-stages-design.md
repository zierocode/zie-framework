---
approved: true
approved_at: 2026-04-15
backlog: backlog/parallel-pipeline-stages.md
---

# Parallel Pipeline Stages — Design Spec

**Problem:** Sprint Phase 1 runs spec+plan for multiple items sequentially within a single context, even though items are independent. Each Skill call blocks the next, wasting wall-clock time on what could be concurrent work. The sprint command says "parallel Skill calls" but Claude Code processes them sequentially — true parallelism requires Agent spawning.
**Approach:** Change sprint Phase 1 to spawn background agents (one per item) for the full spec+plan pipeline, with a concurrency cap of 4 to limit token explosion. Each agent runs spec-design → write-plan → plan-review → approve independently. The main sprint context orchestrates spawning and collects results. Implementation stays WIP=1. No changes to /spec, /plan, or reviewer skills.
**Components:**
- `commands/sprint.md` — restructure Phase 1 to use Agent spawning with concurrency cap; update ROADMAP mutation pattern; update sprint-context.json aggregation
- `skills/spec-design/SKILL.md` — no change (already supports autonomous mode)
- `skills/write-plan/SKILL.md` — no change (already supports standalone invocation)
- `skills/plan-review/SKILL.md` — no change (already inline)
- `skills/spec-review/SKILL.md` — no change (already inline)
**Data Flow:**

*Current flow (sequential Skill calls within single context):*
1. For each item in needs_spec: invoke spec-design Skill → wait → invoke write-plan Skill → wait → invoke plan-review Skill → wait → approve
2. Next item: same sequence, blocked by previous item
3. Total wall-clock time: sum of all items

*Proposed flow (parallel Agent spawning with concurrency cap):*
1. Compute concurrency cap (default: min(4, number of items))
2. For each item in needs_spec: spawn Agent with `subagent_type: "general-purpose"` and `run_in_background: true`
   - Each agent runs the full pipeline: spec-design (autonomous, runs spec-review inline) → write-plan → plan-review (inline) → approve.py (marks spec+plan as approved)
   - Agent prompt includes: backlog slug, context_bundle, autonomous flag
3. Up to `cap` agents run concurrently; excess items queue until slots open
4. Main sprint context collects results as agents complete
5. Any item that fails → inline retry once (within the agent) → if still failing → surface to main sprint context
6. After all agents complete → update ROADMAP (single batch write, not per-agent)
7. Write sprint-context.json with aggregated specs/plans/keywords

**Edge Cases:**
- **Agent fails mid-pipeline:** Each agent is self-contained. If an agent fails during spec-design or write-plan, it retries once inline. If still failing, it returns failure to the main sprint context, which surfaces the error and halts.
- **Concurrency cap exceeded:** If more items than the cap (default 4), excess items queue and start as slots become available. This balances speed vs. token cost — 4 concurrent agents each reading context is 4x the tokens of 1, but wall-clock time is reduced to ~1/4.
- **Context window overflow in main context:** The main sprint context stays lean — it only orchestrates spawning and collects results. Each agent gets a fresh forked context, so context overflow in one agent doesn't affect others.
- **Inline reviewer compatibility:** Each agent runs its own spec-review and plan-review inline (ADR-054/ADR-058). No conflict between items' reviewers — each agent has its own context.
- **ROADMAP mutations:** Multiple agents must not write ROADMAP concurrently. Solution: main sprint context updates ROADMAP once after all agents complete, not per-agent. Agents write spec/plan files (no conflict — different files) and run approve.py (no conflict — different files). ROADMAP is written by main context only.
- **approve.py concurrency:** Each agent runs approve.py on its own spec/plan file. No conflict since files are different. approve.py is idempotent.
- **Sprint resume:** If sprint context overflows during Phase 1, `.sprint-state` tracks completed items. On resume, completed agents are skipped, incomplete agents are re-spawned.
- **Single item:** If only 1 item needs spec+plan, no parallelism needed — run as a single Skill call (current behavior, no agent spawning overhead).
- **Deeper thinking additions:** The Considerations (backlog), Blind Spots (spec-design), and Risk Review (write-plan) additions from the "deeper-thinking" spec are all inline prompts within each agent — no conflict with parallel execution.

**Out of Scope:**
- Parallel implementation (Phase 2 stays WIP=1 per existing sprint design)
- Parallel release or retro (single batch operations)
- Changes to /spec or /plan commands (they handle single items)
- Changes to reviewer skills (they already run inline)
- Token budget tracking or measurement (throttling is by concurrency cap, not token counting)
- Agent model selection or effort routing within agents (agents inherit the sprint's model)
- Changes to /backlog, /implement, or other commands