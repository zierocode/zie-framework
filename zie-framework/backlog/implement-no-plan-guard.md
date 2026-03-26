---
id: implement-no-plan-guard
title: /zie-implement guard — block if no approved plan in Ready lane
priority: medium
created: 2026-03-27
source: deep-analysis-2026-03-27
---

## Problem

`/zie-implement` can run even when no approved plan exists in the Ready lane of ROADMAP.md.
This breaks the spec-first pipeline: a developer can bypass spec → plan → review gates and
jump straight to implementation.

## Motivation

Enforce the SDLC contract. If no plan is Ready, the correct path is `/zie-plan` first.
This is a critical guardrail for spec-driven development integrity.

## Acceptance Criteria

- [ ] `/zie-implement` reads ROADMAP.md Ready lane at startup
- [ ] If Ready lane is empty: emit clear error — "No approved plan in Ready lane. Run /zie-plan first." and stop
- [ ] If Now lane already has an active item: emit "WIP=1 active. Finish or release before starting new work." and stop
- [ ] Guard is idempotent (safe to re-run when state is valid)
- [ ] Unit test: `test_implement_blocks_without_ready_plan`
- [ ] Unit test: `test_implement_blocks_with_active_now_item`

## Scope

- `commands/zie-implement.md` — add pre-flight check block
- `hooks/utils.py` — expose `parse_roadmap_ready()` helper (reuse existing pattern)
- `tests/unit/test_hooks_*.py` or new `test_commands_implement.py`
