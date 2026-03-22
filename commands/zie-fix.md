# /zie-fix — Bug Fix Path

Fast path for fixing bugs. Skips brainstorming and planning — goes directly to debugging, regression test, fix, and verify. Use this instead of /zie-build for bugs and regressions.

## Pre-flight

1. Read `zie-framework/.config` → project_type, test_runner.
2. If `zie_memory_enabled=true`:
   - Search brain for similar bug patterns: `recall "<bug description>"`

## Steps

### Phase 1 — Understand the bug

3. If bug description provided as argument → use it.
   If not → ask: "What's the bug? Paste error output or describe the behavior."

4. Invoke `Skill(superpowers:systematic-debugging)`:
   - Reproduce the bug
   - Isolate the root cause (not just the symptom)
   - Confirm the minimal reproduction case

### Phase 2 — Regression test first (TDD)

5. Write a failing test that captures the bug:
   - Test name: `test_<bug_slug>` or `test_should_<expected_behavior>`
   - Run: `make test-unit` → confirm test FAILS (reproduces the bug).
   - Never fix before writing the test.

### Phase 3 — Fix

6. Implement the minimal fix:
   - Change only what's needed to fix the root cause.
   - No refactoring unrelated code.
   - Run: `make test-unit` → confirm regression test now PASSES.
   - Run: full `make test-unit` → confirm no regressions introduced.

### Phase 4 — Verify

7. Invoke `Skill(superpowers:verification-before-completion)`.

8. If `has_frontend=true` and bug is UI-related:
   - Start dev server and verify visually with agent-browser if needed.

### Phase 5 — Document + Learn

9. Update ROADMAP.md if bug was tracked there (move to Done).

10. If `zie_memory_enabled=true`:
    - Store fix pattern: `remember "Bug: <description>. Root cause: <cause>. Fix: <approach>. Regression test: <test name>." priority=auto tags=[bug, fix, <module-slug>] project=<project>`

11. Print:
    ```
    Bug fixed: <description>
    Root cause: <cause>
    Fix: <brief description>
    Regression test: <test name> ✓

    Run /zie-ship when ready to release.
    ```

## Notes
- Always write the regression test BEFORE fixing — this is non-negotiable
- If the bug reveals a design problem → after fixing, run /zie-idea to plan a proper solution
- Never use /zie-fix for features — use /zie-build
