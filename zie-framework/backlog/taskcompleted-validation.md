# Backlog: TaskCompleted Hook — Quality Gate Before Task Marked Done

**Problem:**
When Claude marks a Task as completed (TaskUpdate status=completed), there's no
gate to verify the task was actually finished to the required standard. Tasks
get marked done even if tests are failing or acceptance criteria weren't checked.

**Motivation:**
`TaskCompleted` hook fires before a task is marked complete. Returning exit
code 2 blocks the completion and feeds stderr back to Claude as a reason to
continue. This creates a genuine quality gate: if tests fail, the task can't
be marked done.

**Rough scope:**
- New hook: `hooks/task-completed-gate.py` (TaskCompleted event)
- Check: does `.pytest_cache/v/cache/lastfailed` have entries? If yes → block
- Check: does `git status --short` show uncommitted implementation files? → warn
- Output: specific failure reason via stderr (exit code 2 blocks completion)
- Must be fast (< 2s) — run only `make test-unit -q` subset check via cache
  inspection, not full suite
- Gate is advisory for docs/plan tasks: only enforce for tasks with
  "implement" or "fix" in the subject
- Tests: failing tests block, passing tests allow, docs tasks skip gate
