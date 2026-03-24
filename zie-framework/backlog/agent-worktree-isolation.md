# Backlog: Agent isolation:worktree + background:true for Parallel Review

**Problem:**
When zie-implement runs multiple reviewer agents in sequence, each one reads
files that may be mid-edit. A reviewer checking impl against spec sees the
current (possibly broken) state of files, not the clean committed state.

**Motivation:**
Custom agents support `isolation: worktree` — the agent gets a temporary git
worktree copy of the repo. Changes made don't affect the working tree, and the
agent sees the committed state. `background: true` makes agents run async so
multiple reviewers can run in parallel without blocking.

**Rough scope:**
- Update spec-reviewer agent: add `isolation: worktree` (reads clean commits)
- Update impl-reviewer agent: add `background: true` (runs async during
  REFACTOR phase, returns while Claude continues next task)
- Update /zie-implement to handle async reviewer responses (check on next
  turn rather than blocking)
- Document the worktree cleanup behavior (auto-cleaned if no changes)
- Tests: worktree created for spec-reviewer, background agent spawns correctly
