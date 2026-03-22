---
name: tdd-loop
description: TDD RED-GREEN-REFACTOR loop guide for zie-framework builds
type: process
---

# TDD Loop — RED → GREEN → REFACTOR

Use this skill during /zie-build for every task. This is a rigid process skill — follow exactly.

## The Loop

### RED — เขียน test ที่ล้มเหลว

1. Read the task acceptance criteria from the plan.
2. Write a test that:
   - Tests the behavior (not the implementation)
   - Has a clear, descriptive name: `test_should_<expected_behavior>`
   - Covers one thing only
   - Uses the simplest possible setup
3. Run the test → it MUST fail. If it passes, the feature already exists — skip to next task.
4. Confirm you understand WHY it fails (not just that it fails).

### GREEN — ทำให้ test ผ่าน

5. Write the MINIMUM code to make the test pass.
   - No extra features
   - No optimization yet
   - Hardcoding is OK here if needed to get green
6. Run the test → it MUST pass.
7. Run the full unit suite → must not regress anything.

### REFACTOR — ปรับปรุง code

8. Remove duplication.
9. Improve names (variables, functions, parameters).
10. Simplify logic where obvious.
11. Run tests again → must still pass.
12. If refactor reveals a design problem → note it but don't fix it now (add to backlog).

## กฎที่ต้องทำตาม

- Never skip RED. Never write implementation before the failing test.
- Never fix the test to make it pass — fix the code.
- Never comment out failing tests.
- Hardcoding in GREEN is fine; duplication in GREEN is fine. Clean up in REFACTOR.
- One failing test at a time. Don't write 5 failing tests before going GREEN.

## Cycle Time Target

Each RED→GREEN→REFACTOR cycle should take < 15 minutes.
If stuck > 15 minutes on GREEN → stop, invoke systematic-debugging skill.

## Test Quality Checklist

- [ ] Test name describes expected behavior, not implementation
- [ ] One assertion (or a few closely related)
- [ ] Test is isolated (no shared state between tests)
- [ ] Test runs in < 1 second
- [ ] Test fails for the right reason (not setup errors)
