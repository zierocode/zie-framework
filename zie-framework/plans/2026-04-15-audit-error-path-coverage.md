---
date: 2026-04-15
status: approved
slug: audit-error-path-coverage
---

# Implementation Plan: audit-error-path-coverage

## Steps

1. **Add error-path tests for stop-handler** — Test each nudge path when subprocess/git raises: `git log` failure, `git status` failure, missing ROADMAP, missing tests dir, missing sprint flag, missing config. Assert exit 0 and no stdout corruption per ADR-003.

2. **Add error-path tests for session-resume** — Test: missing zie-framework dir, missing VERSION, corrupt MEMORY.md, missing ROADMAP, git log failure, symlink CLAUDE_ENV_FILE, playwright not found, corrupt session memory files. Assert graceful degradation.

3. **Add error-path tests for intent-sdlc** — Test: empty/missing ROADMAP, corrupt roadmap cache, missing config, missing specs dir, missing .zie dir. Assert exit 0 and no crash. Import helper functions (`_extract_roadmap_slugs`, `_spec_approved`, `_check_pipeline_preconditions`) and test with missing/bad inputs.

4. **Add error-path tests for utils_roadmap** — Test: missing file paths, corrupt JSON cache, PermissionError on write, empty decisions dir, non-date strings in Done section. All public functions should return empty/default on error, never raise.

5. **Add error-path tests for auto-test** — Test: missing test runner config, empty test dirs, subprocess timeout, missing project tmp files. Assert exit 0.

6. **Add error-path tests for remaining 10 hooks** — sdlc-compact, safety-check, safety_check_agent, subagent-context, failure-context, session-cleanup, notification-log, reviewer-gate, design-tracker, session-learn. One test class per hook, at least one `@pytest.mark.error_path` test each covering the main except path.

7. **Run `make test-fast`** — Verify all new tests pass and no regressions.

8. **Run `pytest --collect-only -q -m error_path`** — Confirm all 15 hooks have >= 1 error-path test collected.

## Tests

- Each hook gets `@pytest.mark.error_path` decorated tests
- Pattern: monkeypatch dependency to raise exception → call hook/function → assert exit 0 or graceful return
- Helper: `subprocess.run()` based integration tests for hooks, `monkeypatch`/`tmp_path` based unit tests for imported functions
- Coverage gate: `check_error_path_coverage.py` must report PASS

## Acceptance Criteria

- [ ] All 15 in-scope hooks have >= 1 `@pytest.mark.error_path` test
- [ ] `check_error_path_coverage.py` reports PASS
- [ ] `make test-fast` passes with zero failures
- [ ] No change to hook source code (tests only)
- [ ] Each test validates ADR-003: hook exits 0 even on error