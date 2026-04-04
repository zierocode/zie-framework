---
name: tdd-loop
description: TDD RED-GREEN-REFACTOR loop guide for zie-framework builds
user-invocable: false
argument-hint: ""
model: haiku
effort: low
---

# TDD Loop — RED → GREEN → REFACTOR

Use this skill during /implement for every task. This is a rigid process
skill — follow exactly.

## The Loop

### RED — เขียน test ที่ล้มเหลว

1. Read the task acceptance criteria from the plan.
2. Write a test that:
   - Tests the behavior (not the implementation)
   - Has a clear, descriptive name: `test_should_<expected_behavior>`
   - Covers one thing only
   - Uses the simplest possible setup
3. Run the test → it MUST fail. If it passes, the feature already exists — skip
   to next task.
   Run: `make test-fast` — must FAIL
4. Confirm you understand WHY it fails (not just that it fails).

### GREEN — ทำให้ test ผ่าน

1. Write the MINIMUM code to make the test pass.
   - No extra features
   - No optimization yet
   - Hardcoding is OK here if needed to get green
2. Run: `make test-fast` — must PASS (confirms both new test green + no regressions).

### REFACTOR — ปรับปรุง code

1. Remove duplication.
2. Improve names (variables, functions, parameters).
3. Simplify logic where obvious.
4. Run: `make test-ci` — must still pass (full suite).
5. If refactor reveals a design problem → note it but don't fix it now (add to
   backlog).

## กฎที่ต้องทำตาม

- Never skip RED. Never write implementation before the failing test.
- Never fix the test to make it pass — fix the code.
- Never comment out failing tests.
- Hardcoding in GREEN is fine; duplication in GREEN is fine. Clean up in
  REFACTOR.
- One failing test at a time. Don't write 5 failing tests before going GREEN.

## Test Quality Checklist

- [ ] Test name describes expected behavior, not implementation
- [ ] One assertion (or a few closely related)
- [ ] Test is isolated (no shared state between tests)
- [ ] Test runs in < 1 second
- [ ] Test fails for the right reason (not setup errors)
