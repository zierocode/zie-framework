---
approved: true
approved_at: 2026-03-24
backlog: backlog/agent-worktree-isolation.md
---

# Agent isolation:worktree + background:true Parallel Review — Design Spec

**Problem:** Reviewer agents invoked during `/zie-implement` read files from the live working tree, which may be mid-edit, causing reviewers to evaluate partially-written or inconsistent state rather than the clean committed snapshot.

**Approach:** Add `isolation: worktree` to `agents/spec-reviewer.md` and `agents/plan-reviewer.md` so those agents always operate on the last committed state — insulating them from in-progress edits. Add `background: true` to `agents/impl-reviewer.md` so the impl-reviewer runs asynchronously during the REFACTOR phase, allowing `/zie-implement` to continue to the next task rather than blocking. Update `/zie-implement` to check async reviewer results on the next turn rather than inline, preserving the existing max-3-iteration retry gate.

**Components:**
- Modify: `agents/spec-reviewer.md` — add `isolation: worktree` to frontmatter
- Modify: `agents/plan-reviewer.md` — add `isolation: worktree` to frontmatter
- Modify: `agents/impl-reviewer.md` — add `background: true` to frontmatter
- Modify: `commands/zie-implement.md` — replace inline blocking invocation of `@agent-impl-reviewer` with async spawn + deferred result-check protocol
- Create: `zie-framework/specs/2026-03-24-agent-worktree-isolation-design.md` — this file
- Modify: `zie-framework/project/components.md` — document worktree and background fields in the Agents section

**Data Flow:**

1. `/zie-spec` invokes `@agent-spec-reviewer`. Claude Code spawns the agent in a temporary git worktree pointing to `HEAD` (last commit). The working tree's uncommitted changes are invisible to the agent. Agent reads spec file from the clean snapshot, runs Phase 1–3, returns verdict. Worktree is auto-cleaned after agent exits (no changes written = automatic cleanup by Claude Code runtime).

2. `/zie-plan` invokes `@agent-plan-reviewer`. Same worktree isolation as spec-reviewer — agent reads plan file and referenced spec from committed state. Verdict returned synchronously to `/zie-plan` for retry loop.

3. `/zie-implement` — REFACTOR phase per task:
   a. `/zie-implement` invokes `@agent-impl-reviewer` with `background: true`, passing: task description, Acceptance Criteria, and list of files changed in this task.
   b. Claude Code spawns the impl-reviewer agent asynchronously — call returns immediately with a background job handle / task ID.
   c. `/zie-implement` records the pending review in the active task's `TaskUpdate` metadata field (e.g., `reviewer_status: pending, reviewer_task_id: <id>`).
   d. `/zie-implement` proceeds to announce the next task (does not block).
   e. At the start of each subsequent task loop iteration, `/zie-implement` checks the background reviewer result via `TaskGet` on the stored task ID:
      - `reviewer_status: pending` — agent still running; continue current task, check again next iteration.
      - `reviewer_status: approved` — clear; no action needed.
      - `reviewer_status: issues_found` — halt current task, surface reviewer feedback to human, apply fixes, re-invoke `@agent-impl-reviewer` synchronously (blocking) for the fix iteration. Max 3 total iterations still applies (background spawn counts as iteration 1).
   f. After the final task in the plan, `/zie-implement` waits for any still-pending background reviewer before running the final `make test-unit` + `Skill(zie-framework:verify)` sequence.

4. Worktree cleanup: `isolation: worktree` agents that write no files have their worktree auto-removed by Claude Code runtime on exit. No manual cleanup hook needed. If the agent writes a file (unexpected), the worktree persists until the next Claude Code session GC pass — this is safe and expected runtime behavior.

**Edge Cases:**

- **Agent file predates this change (no `isolation` field)** — frontmatter field omission means no isolation; existing behavior preserved. No breaking change for installs that haven't pulled the update.
- **Uncommitted files needed by spec-reviewer** — spec file itself must be committed before `/zie-spec` invokes the agent, or the agent will see a missing file. `/zie-spec` already commits spec at end of the spec-design skill; reviewer is invoked after commit. No conflict.
- **background: true not supported by Claude Code version** — if the runtime ignores `background: true`, the agent runs synchronously (blocking). Behavior degrades gracefully to current behavior; no error.
- **isolation: worktree not supported** — if runtime ignores the field, agent reads live working tree. Behavior degrades to current (pre-fix) behavior — worse but not broken. No error path needed.
- **Background reviewer returns issues on the last task** — `/zie-implement` final-wait step (step 3f) catches this. Fix-iterate loop runs synchronously before the verify+commit sequence.
- **Background reviewer still pending when implement finishes all tasks** — final-wait step blocks until result arrives. If agent hangs beyond a reasonable timeout (e.g., >120s), surface to human: "impl-reviewer did not return — review manually before committing."
- **Multiple background reviewer jobs in flight** — if the plan has many short tasks, several reviewers may be pending simultaneously. `/zie-implement` tracks all pending task IDs in a list; the per-task check and final-wait loop over the full list.
- **TaskUpdate metadata not available** — if `TaskUpdate` does not support freeform metadata fields, store pending reviewer task IDs in a local in-memory list within the `/zie-implement` session. No disk state needed.
- **Worktree path collision** — Claude Code runtime manages worktree paths; no user-controlled path is specified. No collision risk from the agent definition.
- **impl-reviewer requires live files (e.g., to run make test)** — `agents/impl-reviewer.md` has `Bash(make test*)` in its allowed tools. With `background: true` but no `isolation: worktree`, the impl-reviewer runs in the main worktree and can access live files and run tests normally. Do NOT add `isolation: worktree` to impl-reviewer — it needs the current (post-REFACTOR) file state to verify tests pass.

**Out of Scope:**

- Adding `isolation: worktree` to `agents/impl-reviewer.md` — impl-reviewer must see the post-REFACTOR file state and run `make test*`; worktree isolation would show stale committed state, defeating the review purpose.
- Changing reviewer logic, checklist items, Phase 1–3 structure, or output format — this feature only modifies agent frontmatter and invocation protocol.
- Parallelising spec-reviewer or plan-reviewer with `background: true` — those reviewers block their respective commands by design (spec must be approved before plan, plan before implement); async adds no value.
- Implementing a custom worktree manager or cleanup hook — Claude Code runtime handles worktree lifecycle automatically.
- Changing the max-3-iteration retry limit — background spawn counts as iteration 1; logic is unchanged.
- Adding timeout configuration as a user-facing `.config` key — the 120s hardcoded threshold in the final-wait step is a command-level constant, not a project config option.
- Migrating skills (tdd-loop, debug, verify, etc.) to use worktree or background modes — out of scope for this feature.
