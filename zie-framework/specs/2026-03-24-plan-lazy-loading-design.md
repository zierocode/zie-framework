---
approved: true
approved_at: 2026-03-24
backlog: backlog/plan-lazy-loading.md
---

# Plan Lazy Loading — Design Spec

**Problem:** `/zie-implement` reads the entire plan file at startup — including full code blocks and RED/GREEN/REFACTOR steps for every task. A plan with 8 tasks can be hundreds of lines loaded before any work starts. Tasks 4–8 are irrelevant until tasks 1–3 complete.

**Approach:** Two-stage read pattern. At startup: read only the plan header (Goal, Architecture notes, task name list — first ~20 lines). Before starting Task N: read that task's full section (Acceptance Criteria, files, steps). No future task detail is loaded until it becomes active.

**Components:**
- Modify: `commands/zie-implement.md` — replace single full-plan read at startup with header-only read; add per-task section read immediately before executing that task; define header as everything before the first `### Task` heading

**Acceptance Criteria:**
- [ ] Only plan header loaded at session start (goal, architecture, task names)
- [ ] Full task body (AC, files, steps) loaded just before that task executes
- [ ] No task's detail loaded before it is the active task
- [ ] Context footprint measurably smaller for plans with 4+ tasks
- [ ] Plan file format and content unchanged — read strategy only
- [ ] `/zie-plan` approval flow (which needs full plan) unchanged

**Out of Scope:**
- Changing the plan file format
- Lazy loading for `/zie-plan` approval step (user needs to see the full plan)
