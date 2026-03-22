---
approved: true
approved_at: 2026-03-22
backlog: backlog/test-pyramid-skill.md
---

# test-pyramid Skill in /zie-build — Implementation Plan

> **For agentic workers:** Use /zie-build to implement this plan task-by-task with TDD RED/GREEN/REFACTOR loop.

**Goal:** Make /zie-build invoke `Skill(zie-framework:test-pyramid)` before the RED phase of each task so the agent knows which test level to write first.

**Architecture:** A single-line addition to step 8 (RED phase) of `commands/zie-build.md`. The skill invocation is conditional — it fires once per task before the first test is written, providing pyramid guidance (unit / integration / e2e) based on the task type and project config.

**Tech Stack:** Markdown command files, pytest

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `commands/zie-build.md` | Add skill invocation to step 8 (RED phase) |
| Modify | `tests/unit/test_sdlc_gates.py` | Add `TestZieBuildTestPyramid` class |

---

## Task 1: Write failing tests (RED)

Add class `TestZieBuildTestPyramid` to `tests/unit/test_sdlc_gates.py`.

The tests assert that `commands/zie-build.md` step 8 references the test-pyramid skill. All tests must FAIL before implementation because the current step 8 has no mention of `test-pyramid`.

```python
class TestZieBuildTestPyramid:
    def test_build_invokes_test_pyramid_skill(self):
        content = read("commands/zie-build.md")
        assert "test-pyramid" in content, \
            "/zie-build step 8 must invoke Skill(zie-framework:test-pyramid)"

    def test_build_pyramid_skill_uses_correct_namespace(self):
        content = read("commands/zie-build.md")
        assert "zie-framework:test-pyramid" in content, \
            "/zie-build must reference the skill with full namespace zie-framework:test-pyramid"

    def test_build_pyramid_invocation_is_in_red_phase(self):
        content = read("commands/zie-build.md")
        # Confirm test-pyramid appears in proximity to the RED phase heading
        red_pos = content.find("RED phase")
        pyramid_pos = content.find("test-pyramid")
        assert red_pos != -1 and pyramid_pos != -1, \
            "/zie-build must have both a RED phase and test-pyramid reference"
        # test-pyramid must appear after RED phase heading and before GREEN phase
        green_pos = content.find("GREEN phase")
        assert red_pos < pyramid_pos < green_pos, \
            "test-pyramid skill invocation must be inside the RED phase (between RED and GREEN)"

    def test_build_pyramid_guides_test_level(self):
        content = read("commands/zie-build.md")
        assert "unit" in content and "integration" in content and "e2e" in content, \
            "/zie-build must mention unit/integration/e2e levels (guided by test-pyramid)"
```

Run: `make test-unit` — all 4 tests in `TestZieBuildTestPyramid` must fail.

---

## Task 2: Implement (GREEN)

In `commands/zie-build.md`, update step 8 (RED phase) by prepending the skill invocation line. The current step 8 reads:

```text
8. **RED phase** — Write failing test first:
   - Create or update test file matching the module being implemented.
```

Add one instruction as the first bullet under step 8:

```markdown
8. **RED phase** — Write failing test first:
   - Before writing the test, invoke `Skill(zie-framework:test-pyramid)` to determine the right test level (unit / integration / e2e) for this task type. Use the pyramid guidance to decide which level to start with.
   - Create or update test file matching the module being implemented.
   - Test must fail before any implementation.
   - Run: `make test-unit` → confirm test fails (expected).
   - If test already passes → the feature already exists, move to next task.
```

Run: `make test-unit` — all 4 tests in `TestZieBuildTestPyramid` must now pass.

---

## Task 3: Full suite

Run the full test suite to confirm no regressions:

```bash
make test-unit
```

Expected: all existing classes (`TestZieInitBacklog`, `TestZieShipMemory`, `TestZieRetroMemory`, `TestIntentDetectPlan`, `TestZieBuildGates`, `TestZiePlanCommand`, `TestZieIdeaBacklogFirst`, `TestROADMAPReadyLane`) continue to pass alongside the new `TestZieBuildTestPyramid`.

Note: the existing `TestZieBuildGates` tests must still pass — the new line does not affect WIP gate, approved plan gate, parallel agents, or depends_on logic.

---

## Context from brain

_No prior memories on this feature. First implementation._
