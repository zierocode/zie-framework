---
slug: audit-test-hardening
approved: true
approved_at: 2026-03-23
backlog: backlog/audit-test-hardening.md
---

# Spec: Test Hardening

## Problem

Tests across `test_hooks_auto_test.py` and `test_hooks_wip_checkpoint.py` write to shared `/tmp/zie-*` paths without any teardown fixture, causing non-deterministic failures when stale state from one test bleeds into another. Intent-detect assertions use substring matching (`"/zie-fix" in r.stdout`) instead of parsing the JSON output contract, meaning a silent protocol regression would not be caught. Several critical code paths — frontmatter/long-message suppression guards, `find_matching_test()` logic, ROADMAP edge cases, and debounce boundary values — have zero test coverage.

## Approach

Introduce `@pytest.fixture(autouse=True)` teardown blocks in every test class that touches `/tmp/zie-*` files; this makes cleanup structural and inherited by any future test added to those classes. Replace substring assertions in `TestIntentDetectHappyPath` with `json.loads(r.stdout)["additionalContext"]` lookups to validate the actual Claude Code hook JSON contract. Import `find_matching_test()` directly from `auto-test.py` using `importlib` (or `sys.path` injection) to enable pure unit tests with no subprocess overhead. Add dedicated test classes for the frontmatter/long-message skip guards, ROADMAP edge cases, and debounce boundary values (`debounce_ms=0` and `debounce_ms=999999`).

## Acceptance Criteria

- [ ] AC-1: `TestAutoTestDebounce` and `TestAutoTestRunnerSelection` in `test_hooks_auto_test.py` each have an `autouse=True` fixture that deletes `/tmp/zie-framework-last-test` after every test.
- [ ] AC-2: `TestWipCheckpointCounter` in `test_hooks_wip_checkpoint.py` has an `autouse=True` fixture that deletes `/tmp/zie-framework-edit-count` after every test, replacing the manual `reset_counter()` calls.
- [ ] AC-3: All happy-path assertions in `TestIntentDetectHappyPath` use `json.loads(r.stdout)["additionalContext"]` and assert the expected `/zie-*` command value, not a substring of raw stdout.
- [ ] AC-4: A new test class `TestIntentDetectSkipGuards` covers the frontmatter skip: a prompt starting with `"---"` produces empty stdout even in a valid `zie-framework` cwd.
- [ ] AC-5: `TestIntentDetectSkipGuards` also covers the long-message skip: a prompt of 501+ characters produces empty stdout.
- [ ] AC-6: A new test class `TestFindMatchingTest` imports `find_matching_test()` directly (no subprocess) and asserts correct return values for: a matching `test_{stem}.py` found recursively, no match returning `None`, and a vitest/jest stem resolving a `.test.ts` candidate.
- [ ] AC-7: A new test class `TestWipCheckpointRoadmapEdgeCases` covers: missing `ROADMAP.md` (no crash), a `ROADMAP.md` with an empty `## Now` section (no checkpoint triggered), and a `## Now` block with malformed (non-list) items (graceful skip).
- [ ] AC-8: A new test class `TestAutoTestDebounceBoundary` covers `debounce_ms=0` (debounce file present but always runs — elapsed always >= 0 ms) and `debounce_ms=999999` (debounce file with mtime=now always suppresses).
- [ ] AC-9: Every test file that touches `/tmp/zie-*` paths uses the same standardized `autouse=True` fixture pattern — no ad-hoc `if exists: unlink()` calls outside of that fixture.
- [ ] AC-10: All existing tests continue to pass with no behavioral changes.

## Out of Scope

- Adding tests for hooks not mentioned (e.g., `session-learn.py` ROADMAP edge cases are out of scope for this hardening pass unless trivially co-located).
- Refactoring hook source code to aid testability (import structure changes to `auto-test.py` are limited to what is necessary to expose `find_matching_test()`).
- Converting subprocess-based tests to direct imports wholesale — only `find_matching_test()` warrants direct import due to its pure, side-effect-free signature.

## Files Changed

- `tests/unit/test_hooks_auto_test.py` — add `autouse` teardown fixtures, `TestFindMatchingTest`, `TestAutoTestDebounceBoundary`
- `tests/unit/test_hooks_wip_checkpoint.py` — replace `reset_counter()` calls with `autouse` teardown fixture, add `TestWipCheckpointRoadmapEdgeCases`
- `tests/unit/test_hooks_intent_detect.py` — strengthen happy-path assertions to JSON parse, add `TestIntentDetectSkipGuards`
