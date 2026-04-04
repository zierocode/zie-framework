# Plan: subagent-context — Skip Plan File Read for Explore Agents

**Slug:** `subagent-context-explore-guard`
**Spec:** `specs/2026-04-04-subagent-context-explore-guard-design.md`
**Date:** 2026-04-04

## Tasks

### Task 1 — Update tests (RED)

- [ ] In `tests/unit/test_hooks_subagent_context.py`:
  - Update `test_first_incomplete_task_extracted` — change `agentType` to `"Plan"`,
    assert `Task:` present and plan content visible
  - Update `test_all_tasks_complete_message` — change `agentType` to `"Plan"`
  - Add `test_explore_agent_omits_task_field` — Explore agent, assert `"Task:"` NOT in ctx
  - Add `test_explore_agent_has_active_and_adrs` — Explore agent, assert `Active:` and
    `ADRs:` present
  - Add `test_plan_agent_includes_task_field` — Plan agent with plan file, assert
    `Task:` present and plan step visible
- [ ] Run `make test-fast` — confirm new tests fail (RED)

### Task 2 — Implement guard in hook (GREEN)

- [ ] In `hooks/subagent-context.py`:
  - Pass `agent_type` (already parsed in outer guard) into the inner operations scope
  - Wrap the plan file read block (lines 50–74) with:
    `if not re.search(r'Plan', agent_type, re.IGNORECASE):`  → skip block for Explore
  - When plan block is skipped, set `active_task = "n/a"` (or omit field from payload)
  - Update the `payload` string: emit `Task:` only when `active_task != "n/a"`;
    for Explore agents emit `Active: {feature_slug} | ADRs: {adr_count} ...`
- [ ] Run `make test-fast` — confirm new tests pass (GREEN)

### Task 3 — Verify & lint

- [ ] Run `make lint` — zero violations
- [ ] Run `make test-ci` — full suite green, coverage gate passes

### Task 4 — Docs

- [ ] No `components.md` change needed (hook behaviour, not registration)
- [ ] Confirm `CLAUDE.md` hook table still accurate (no change required)
