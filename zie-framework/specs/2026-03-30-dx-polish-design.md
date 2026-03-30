---
approved: true
approved_at: 2026-03-30
backlog: backlog/dx-polish.md
---

# DX Polish — Design Spec

**Problem:** Users lack visual feedback about their pipeline stage, get stuck when reviewers hit iteration limits, and have no guidance on task granularity — leading to oversized or under-scoped implementation plans.

**Approach:** Add three lightweight UX enhancements that require no architecture changes: (1) `/zie-status` displays an ASCII progress indicator showing which pipeline stage the current feature is in; (2) all three reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) show explicit "next steps" when max iterations (3) are reached; (3) write-plan SKILL.md and plan-reviewer surface task granularity guidance based on scope (1–3 files → 2–3 tasks, 4–8 files → 5–7 tasks, 9+ files → 8–12 tasks, max 15).

**Components:**
- `/zie-status` command (`commands/zie-status.md`)
- `spec-reviewer` skill (`skills/spec-reviewer/SKILL.md`)
- `plan-reviewer` skill (`skills/plan-reviewer/SKILL.md`)
- `impl-reviewer` skill (`skills/impl-reviewer/SKILL.md`)
- `write-plan` skill (`skills/write-plan/SKILL.md`)

**Data Flow:**

### 1. Pipeline Progress Indicator in /zie-status

**Current behavior:** After showing status table, /zie-status prints "Next suggested command".

**New behavior:** Add a "Pipeline" section after status table and before test table:

```markdown
**Pipeline**

backlog ✓ → spec ✓ → plan ✓ → [implement ▶] → release → retro

Current feature: <slug> [ready to release]
```

**Detection logic** (run in step 7 of zie-status.md):

1. Extract active feature slug from Now lane (first `- [ ]` item), e.g., `dx-polish`
2. If no active feature → print `"No active feature — start with: /zie-backlog"`; return early
3. For the active slug, check pipeline progression:
   - **Backlog stage:** `zie-framework/backlog/<slug>.md` exists → ✓
   - **Spec stage:** `zie-framework/specs/YYYY-MM-DD-<slug>-design.md` exists AND contains `approved: true` → ✓
   - **Plan stage:** `zie-framework/plans/YYYY-MM-DD-<slug>.md` exists AND contains `approved: true` → ✓
   - **Implement stage:** Active (in Now lane) → ▶
   - **Release stage:** All tasks in plan marked `[x]` → ✓
   - **Retro stage:** Most recent git tag created after plan's `approved_at` → ✓
4. Build pipeline string: `backlog → spec → plan → implement → release → retro`
   - Mark completed stages with ✓
   - Mark current stage with ▶
   - Enclose current stage in brackets: `[implement ▶]`
   - Leave future stages unmarked
5. Append `Current feature: <slug>` and status note:
   - If all tasks complete → `[pending release]`
   - If some tasks complete → `[<N>/<total> tasks done]`
   - If no tasks started → `[ready to start]`

### 2. Max Iterations "Next Steps" Block in Reviewers

**Current behavior:** When a skill reaches max 3 iterations, output is:

```text
❌ Issues Found
1. [Scope] ...
2. [Gap] ...
Fix these and re-submit for review.
```

**New behavior:** Add an explicit "next steps" block after issues:

```text
❌ Max review iterations reached (3/3)

To continue:
1. Edit <file> to address the issues above
2. Re-run /zie-spec <slug> OR /zie-plan <slug> OR /zie-implement

Or describe the issue to get guidance.
```

**Implementation details:**

- Add to end of Phase 2/3 output in all three reviewers (spec-reviewer, plan-reviewer, impl-reviewer)
- Trigger: iteration counter (passed by caller) == 3
- File name: extract from backlog or slug context
  - For spec-reviewer: use `zie-framework/specs/YYYY-MM-DD-<slug>-design.md`
  - For plan-reviewer: use `zie-framework/plans/YYYY-MM-DD-<slug>.md`
  - For impl-reviewer: use the task's file list
- Command: determine which skill invoked the reviewer and suggest the matching command

### 3. Task Granularity Guidance

**Part A: write-plan SKILL.md** — Add "Task Sizing" section before the task template:

```markdown
## Task Sizing

A good task is completable in one focused session (1–2 hours).

**Simple features** (1–3 files changed, single pattern):
- Recommended: 2–3 tasks
- Example: add a new enum value, update docstring, bump version

**Medium features** (4–8 files, new utility functions or refactor):
- Recommended: 5–7 tasks
- Example: new command with help text, argument parsing, basic test coverage

**Complex features** (9+ files, new subsystem or architecture):
- Recommended: 8–12 tasks
- Example: new skill with full integration (context bundle, file I/O, error handling)

**Maximum recommended: 15 tasks.** If a feature requires >15 tasks, split
it into two smaller backlog items with clear dependency ordering.

If unsure, ask yourself: "Can I complete this task + write tests + refactor
in one session?" If no, split it.
```

**Part B: plan-reviewer SKILL.md** — Add granularity check to Phase 2:

```markdown
4. **Task granularity** — Is each task completable in one focused session? Flag
   tasks that try to do too much at once.

   **New check**: Count total tasks in the plan. If >15 tasks:
   - Surface as a warning (not blocking):
     "Plan has N tasks (>15 recommended max). Consider splitting into two features."
   - Include in Phase 2 Issues Found list, but do not prevent APPROVED verdict.
```

**Edge Cases:**

- `/zie-status` with no active feature: print error and return early (no pipeline shown)
- `/zie-status` with partial pipeline (e.g., backlog + spec only, plan not yet written): show ✓ and → for completed stages, empty space for unfilled, no ▶ yet
- Reviewer iteration counter not provided by caller: default to 0 (no max-reached block shown)
- Task count exactly 15: not flagged (at limit, not over)
- Spec/plan files with malformed frontmatter: graceful skip on date parsing (treat as not approved)
- Circular task dependencies (Task A → B → A): plan-reviewer does not validate circularity; implementation phase will catch via git merge conflicts

**Out of Scope:**

- Changing the max iteration limit (remains 3)
- Visual/graphical UI components or terminal progress bars
- Interactive TUI or color highlighting
- Automatic plan splitting based on task count
- Machine learning task estimation
- API changes to reviewer invocation signatures
