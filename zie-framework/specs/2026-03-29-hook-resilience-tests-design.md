---
approved: true
approved_at: 2026-03-29
backlog: backlog/hook-resilience-tests.md
---

# Hook Resilience Tests — Design Spec

**Problem:** Hook test coverage is heavy on happy paths (1600+ tests) but lacks systematic error-path and edge-case tests, leaving production deployments vulnerable to crashes on uninitialized projects, malformed config, subprocess timeouts, and partial state corruption.

**Approach:** Create five focused test modules that each target a specific failure category (uninitialized project, malformed config, subprocess timeout, partial state, concurrent writes). Each test file uses a shared `run_hook()` helper fixture (following ADR-015 env isolation) and mocks filesystem/subprocess boundaries to exercise error paths. Tests are added to `make test-unit` run, making hook resilience a gated requirement before release.

**Components:**
- `tests/unit/test_hook_uninitialized_project.py` — Create
- `tests/unit/test_hook_malformed_config.py` — Create
- `tests/unit/test_hook_subprocess_timeout.py` — Create
- `tests/unit/test_hook_partial_state.py` — Create
- `tests/unit/test_hook_concurrent_writes.py` — Create
- `tests/conftest.py` — Modify (add shared run_hook helper + fixtures)
- `Makefile` — Modify (add coverage gate: all hooks ≥1 error-path test)

**Data Flow:**

1. Test discovery: pytest collects all five test modules + existing tests.
2. Hook selection: Each test file reads hooks.json to determine which hooks to cover, then constructs isolated tmp directories mimicking broken states (missing zie-framework/, malformed .config, empty ROADMAP.md, etc.).
3. Hook execution: `run_hook()` helper spawns hook subprocess with isolated env (ADR-015), cleared of all session-injected vars, with CLAUDE_CWD pointing to the broken tmp structure.
4. Assertion: Verify hook exits 0 (silent fail) and produces expected stderr log or no-op behavior (no crash, no hang).
5. Coverage gate: After all tests pass, a pytest plugin or post-test script counts error-path tests per hook (via `@pytest.mark.error_path` tags) and fails the suite if any hook has 0 such tests.
6. Release gate: /zie-release calls `make test-unit` which includes the new gate; release fails if coverage is incomplete.

**Edge Cases:**

- `zie-framework/` dir exists but `.config` is empty dict `{}` — hooks should apply defaults, not crash.
- `.config` contains valid JSON but unrecognized keys — hooks should ignore unknown keys, use defaults.
- ROADMAP.md exists but ## Now section is empty (vs missing file) — `parse_roadmap_now()` already handles this, test validates hooks don't re-process it.
- `plans/` dir is missing (vs empty) — `subagent-context.py` should inject default context, not fail.
- `specs/` dir is missing entirely — hooks that read specs should degrade gracefully.
- `safety_check_agent.py` subprocess times out at 5s — should fall back to regex-only check without blocking.
- `auto-test.py` calls `make test-unit` which hangs beyond wall-clock limit — should timeout and exit 0 (not kill the session).
- `session-cleanup.py` deletes `/tmp/zie-<session>` directory while `notification-log.py` attempts to write to `/tmp/zie-<session>/notification.log` — both hooks should handle ENOENT/OSError gracefully and exit 0.
- Project name contains special chars (spaces, @, !, etc.) — `safe_project_name()` sanitizes, hooks use sanitized names correctly.
- `/tmp` is read-only or full — `safe_write_tmp()` returns False, hooks continue gracefully.
- CLAUDE_CWD env var is absent (fallback to os.getcwd()) — hooks should still work (tested via patch).

**Out of Scope:**

- Network failures in zie-memory API calls — already tested in zie-memory, not a hook responsibility.
- Claude Code internal failures (e.g., malformed hook event JSON) — hook contract says exit 0 on any event parse error.
- Performance/load testing under 10k+ files — separate performance audit.
- Symlink attacks on persistent paths — already hardened via ADR-010, tested in test_utils.py.
- Long-running hooks that exceed wall-clock limits beyond `auto-test.py` — auto-test has explicit timeout gate, others should not be long-running.
- Integration tests with real Claude Code session — integration tests are in separate suite, not part of this spec.

**YAGNI Check:**

- Tests do NOT add new runtime error handling — only validate existing error paths.
- Tests do NOT add configurable timeouts or retries — those are out-of-scope (backlog item: hook-config-hardening).
- Tests do NOT refactor hooks themselves — if refactoring is needed, file a separate backlog item.
- Tests do NOT create new utility functions — reuse existing `parse_roadmap_*`, `load_config()`, `safe_write_*` functions.

**Ambiguity Check:**

- "Error path" is defined as: any code path where a hook encounters missing input, malformed data, or subprocess failure, and exits 0 (silent fail) without crashing Claude.
- "Edge case" is defined as: valid project state (or absence of state) that is not covered by existing happy-path tests.
- "All hooks ≥1 error-path test" is enforced by a pytest marker `@pytest.mark.error_path` + post-test coverage script that counts marked tests per hook and fails the suite if count is 0 for any hook.

**Testability:**

Acceptance criteria derived from spec:
- [ ] `test_hook_uninitialized_project.py` exists with ≥6 test cases (one per hook: intent-sdlc, session-resume, auto-test, sdlc-compact, safety-check.py, subagent-context), each verifying hook exits 0 when zie-framework/ is absent.
- [ ] `test_hook_malformed_config.py` exists with ≥4 test cases (empty .config, invalid JSON, unrecognized keys, .config absent but zie-framework/ present).
- [ ] `test_hook_subprocess_timeout.py` exists with ≥2 test cases: safety_check_agent falls back to regex when subprocess timeout, auto-test exits cleanly when make hangs.
- [ ] `test_hook_partial_state.py` exists with ≥4 test cases (ROADMAP.md empty Now, specs/ missing, plans/ missing, PROJECT.md missing).
- [ ] `test_hook_concurrent_writes.py` exists with ≥1 test case (session-cleanup deletes /tmp/zie-<session> while notification-log tries to write, both exit 0 gracefully).
- [ ] `conftest.py` defines shared `run_hook()` helper following ADR-015 env isolation (clear all session-injected vars).
- [ ] All new tests marked with `@pytest.mark.error_path`.
- [ ] `make test-unit` runs new tests and post-test script validates ≥1 error-path test per hook.
- [ ] All tests pass on clean `pytest tests/unit/`.
- [ ] Coverage includes minimum hooks from backlog scope: intent-sdlc.py, session-resume.py, auto-test.py, sdlc-compact.py, safety-check.py, subagent-context.py, safety_check_agent.py, failure-context.py, session-cleanup.py, notification-log.py (10 hooks total).
