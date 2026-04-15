---
name: tdd-loop
description: TDD RED-GREEN-REFACTOR loop guide for zie-framework builds
user-invocable: false
argument-hint: ""
model: haiku
effort: low
---

# TDD Loop — RED → GREEN → REFACTOR

## The Loop

### RED — เขียน test ที่ล้มเหลว

1. Read the task acceptance criteria from the plan.
2. Write a test that:
   - Tests behavior (not implementation)
   - Has clear name: `test_should_<expected_behavior>`
   - Covers one thing only, simplest setup
3. Run `make test-fast` — must FAIL. If passes, feature already exists → skip to next task.
4. Confirm you understand WHY it fails.

### GREEN — ทำให้ test ผ่าน

1. Write MINIMUM code to pass. No extra features, no optimization, hardcoding OK.
2. Run `make test-fast` — must PASS (new test green + no regressions).

### REFACTOR — ปรับปรุง code

1. Remove duplication.
2. Improve names.
3. Simplify obvious logic.
4. Run `make test-ci` — must still pass (full suite).
5. Design problem revealed? → note it, don't fix now (add to backlog).

## กฎที่ต้องทำตาม

- Never skip RED. Never write implementation before the failing test.
- Never fix the test to make it pass — fix the code.
- Never comment out failing tests.
- Hardcoding/duplication in GREEN is fine — clean up in REFACTOR.
- One failing test at a time.
- **Run tests once per phase.** Truncated output → `tail -30`, not a re-run. No code change = no re-run.

## Test Quality Checklist

- [ ] Name describes expected behavior, not implementation
- [ ] One assertion (or a few closely related)
- [ ] Isolated (no shared state)
- [ ] Runs in < 1 second
- [ ] Fails for the right reason (not setup errors)