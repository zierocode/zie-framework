---
description: Implement the active feature using TDD — RED/GREEN/REFACTOR loop per task. Reads active plan from ROADMAP.md.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, TaskCreate, TaskUpdate
---

# /zie-build — TDD Feature Implementation Loop

Implement the active feature using Test-Driven Development. Reads the active plan from ROADMAP.md and guides through RED → GREEN → REFACTOR per task.

## Pre-flight

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/ROADMAP.md` → find first incomplete task in "Now" section.
3. Read corresponding plan file from `zie-framework/plans/`.
4. Read `zie-framework/.config` → project_type, test_runner.
5. If `zie_memory_enabled=true`:
   - Recall relevant memories for current feature → use as context.

## Steps

### Per task (repeat until all tasks complete):

6. **Announce task**: "Working on: [Task N] — <task description>"

7. If `superpowers_enabled=true` and task is non-trivial:
   - Invoke `Skill(superpowers:test-driven-development)` for guidance.

8. **RED phase** — Write failing test first:
   - Create or update test file matching the module being implemented.
   - Test must fail before any implementation.
   - Run: `make test-unit` → confirm test fails (expected).
   - If test already passes → the feature already exists, move to next task.

9. **GREEN phase** — Implement minimum code to pass:
   - Write only enough code to make the test pass.
   - No over-engineering, no speculative features.
   - Run: `make test-unit` → confirm test passes.

10. **REFACTOR phase** — Clean up without breaking tests:
    - Remove duplication, improve naming, simplify.
    - Run: `make test-unit` → confirm still passes.

11. **Mark task complete**:
    - Update `TaskUpdate` → completed.
    - Update plan file: mark task as `[x]`.
    - Update ROADMAP.md task counter if tracking.

12. **Brain checkpoint** (every 5 tasks or on natural stopping point):
    - If `zie_memory_enabled=true`: POST `/api/hooks/wip-update` with current progress.

### After all tasks complete:

13. Run full test suite: `make test-unit` (required) + `make test-int` (if available).

14. Print:
    ```
    All tasks complete for: <feature name>

    Tests: unit ✓ | integration ✓|n/a

    Next: Run /zie-ship to release, or /zie-idea for the next feature.
    ```

## Handling Failures

- If a test fails unexpectedly → invoke `Skill(superpowers:systematic-debugging)` before trying fixes.
- If stuck after 2 attempts → surface the error, explain options, ask Zie which path to take.
- Never silently skip tests or comment them out.

## Notes
- Works for any language — test runner detected from `.config`
- If no active plan in ROADMAP.md → suggest running `/zie-idea` first
- Can be run mid-task to resume after a break
- The PostToolUse:auto-test hook fires on every file save — this command sets the strategic direction, hooks handle the feedback loop
