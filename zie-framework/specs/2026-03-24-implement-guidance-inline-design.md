---
approved: true
approved_at: 2026-03-24
backlog: backlog/implement-guidance-inline.md
---

# Implement Loop — Inline Guidance + Parallel Tasks by Default — Design Spec

**Problem:** `/zie-implement` invokes `Skill(zie-framework:tdd-loop)` and `Skill(zie-framework:test-pyramid)` for every task — two extra model calls per task with near-static output. Additionally, independent tasks run sequentially unless the plan author explicitly annotates `<!-- depends_on: -->`, which rarely happens.

**Approach:** Embed tdd-loop (RED/GREEN/REFACTOR summary) and test-pyramid (unit/integration/e2e decision rule) as inline text printed once at session start. Remove per-task skill invocations for these two. Invert the parallelism default: tasks with no `depends_on` run in parallel; tasks with `<!-- depends_on: T1 -->` run sequentially after the dependency. Keep `Skill(tdd-loop)` invocation for `tdd: deep` hint or unexpected test failure.

**Components:**
- Modify: `commands/zie-implement.md` — replace per-task `Skill(tdd-loop)` and `Skill(test-pyramid)` calls with inline guidance block printed at session start; add parallel-by-default logic for tasks without `depends_on`; preserve conditional skill invocation for `tdd: deep` hint and test failures

**Acceptance Criteria:**
- [ ] `tdd-loop` and `test-pyramid` skills not invoked per task under normal conditions
- [ ] Inline TDD guidance block printed once at session start
- [ ] Tasks without `depends_on` executed in parallel by default
- [ ] Tasks with `<!-- depends_on: TN -->` run sequentially after their dependency
- [ ] `tdd: deep` plan hint still triggers `Skill(zie-framework:tdd-loop)` for that task
- [ ] Unexpected test failure still triggers `Skill(zie-framework:tdd-loop)` for debug

**Out of Scope:**
- Changing the TDD process or what RED/GREEN/REFACTOR means
- Reviewer logic changes
