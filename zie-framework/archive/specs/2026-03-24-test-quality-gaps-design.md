---
approved: true
approved_at: 2026-03-24
backlog: backlog/test-quality-gaps.md
---

# Test Quality: Fill Edge Case and Error Path Gaps — Design Spec

**Problem:** Hook tests have seven categories of missing coverage: subprocess timeout error paths, JSON edge cases, None/empty event inputs, regex pattern unit tests, git-unavailable scenarios, time-boundary tests, and incomplete path traversal coverage. These gaps mean the safety-critical behavior of hooks (blocking dangerous commands, parsing JSON from Claude) is not verified under failure conditions.

**Approach:** Add targeted test cases to existing test files — no new test files, no hook code changes. Each gap maps to specific hooks and specific input conditions. All tests use the existing subprocess invocation pattern (hooks are called as child processes with crafted stdin JSON). Tests are grouped by hook file to keep each test file cohesive. Total: approximately 35 new test methods across 9 existing test files.

**Components:**
- `tests/unit/test_hooks_auto_test.py` — add timeout + empty-config tests
- `tests/unit/test_hooks_task_completed_gate.py` — add timeout + empty-lastfailed tests
- `tests/unit/test_hooks_safety_check.py` — add per-pattern unit tests for all BLOCKS/WARNS
- `tests/unit/test_input_sanitizer.py` — add NUL byte + symlink loop tests (overlaps security-path-traversal spec)
- `tests/unit/test_hooks_sdlc_context.py` — add staleness boundary tests
- `tests/unit/test_hooks_sdlc_compact.py` — add git-unavailable test
- `tests/unit/test_stop_guard.py` — add git-unavailable test
- `tests/unit/test_hooks_wip_checkpoint.py` — add corrupt counter + zie-memory unreachable tests
- `tests/unit/test_hooks_notification_log.py` — add corrupt log file test

**Gap 1 — Subprocess timeout error paths**

Affected files: `auto-test.py:138`, `task-completed-gate.py:61`, `sdlc-compact.py:54,66`, `stop-guard.py:53`

For each hook, add a test that:
- Mocks git to hang (e.g., `git` → script that `sleep 60`)
- Passes a `timeout=N` (N < 60) to the hook subprocess
- Asserts: hook exits 0 (never blocks Claude)
- Asserts: hook stdout is valid JSON or empty (no crash output)

These tests confirm `TimeoutExpired` is caught and handled gracefully per the two-tier error handling pattern.

**Gap 2 — JSON edge cases (corrupt / empty / missing files)**

Affected hooks: any that read `.config`, `.pytest_cache/v/cache/lastfailed`, or counter files.

Test cases to add (one per hook, same input shapes):
- `test_corrupt_config_json` — `.config` file exists but contains `{bad json` → hook exits 0, no crash
- `test_empty_config_json` — `.config` exists with `{}` → hook exits 0, uses all defaults
- `test_empty_lastfailed_dict` (`task-completed-gate`) — lastfailed is `{}` → hook exits 0, allows task completion
- `test_missing_lastfailed_file` (`task-completed-gate`) — cache dir absent → hook exits 0, allows completion
- `test_corrupt_wip_counter` (`wip-checkpoint`) — counter file contains `"not-an-int"` → hook exits 0, resets to 0
- `test_corrupt_notification_log` (`notification-log`) — log file contains one valid JSON line + one `{bad` → hook exits 0, resets or skips corrupt line

**Gap 3 — None / empty event inputs**

Affected hooks: any PreToolUse hook (`safety-check`, `input-sanitizer`, `stop-guard`).

Test cases:
- `test_none_tool_input` — event JSON has `"tool_input": null` → hook exits 0
- `test_missing_tool_name` — event JSON has no `"tool_name"` key → hook exits 0
- `test_empty_command` — Bash event with `"command": ""` → hook exits 0
- `test_malformed_event_not_dict` — stdin contains `"just a string"` (not a JSON object) → hook exits 0

**Gap 4 — Regex pattern unit tests for BLOCKS/WARNS**

Affected file: `hooks/safety-check.py` (BLOCKS: 11 patterns, WARNS: 2 patterns).

Strategy: import `safety_check.evaluate()` directly (it's already a named function, not module-level code). Test each pattern individually:

```python
from hooks.safety_check import evaluate  # direct import (after coverage migration)
```

One `@pytest.mark.parametrize` for BLOCKS (each should return 2):
- `rm -rf /`
- `rm -rf ~`
- `rm -rf .`
- `DROP DATABASE mydb`
- `DROP TABLE users`
- `TRUNCATE TABLE events`
- `git push --force`
- `git push -f`
- `git push origin main`
- `git push origin master`
- `git reset --hard HEAD~1`
- `git commit --no-verify`

One parametrize for WARNS (each should return 0 with warning text in stdout):
- `docker compose down --volumes`
- `alembic downgrade base`

Additional cases:
- `git push origin feature-branch` (should NOT be blocked — not main/master, assert returncode == 0)
- `git push --force-with-lease` (assert returncode == 2 — `--force-with-lease` matches `--force\b` because `\b` is a word/non-word boundary between `e` and `-`)

**Gap 5 — Git unavailable in hooks that call git**

Affected: `sdlc-compact.py`, `stop-guard.py` (in addition to `failure-context.py` which already has this test).

Pattern: set `PATH` to a temp dir where git doesn't exist, assert hook exits 0 with degraded-but-non-crashing behavior. Mirror the existing pattern in `test_hooks_failure_context.py:141-150`.

**Gap 6 — Time-boundary staleness test**

Affected: `sdlc-context.py` (STALE_THRESHOLD=300 seconds).

Create a ROADMAP snapshot file with mtime set to:
- 299 seconds ago → assert context is NOT considered stale (snapshot used)
- 300 seconds ago → boundary — assert behavior matches whichever side the code is on (`<` vs `<=`)
- 301 seconds ago → assert context IS stale (snapshot ignored, file re-read)

Use `os.utime()` to set file mtime.

**Gap 7 — File I/O and argument validation**

- `test_wip_checkpoint_memory_unreachable` (`wip-checkpoint`) — `ZIE_MEMORY_API_URL` points to `http://localhost:19999` (nothing listening) → hook exits 0
- `test_stop_guard_rename_arrow_in_filename` (`stop-guard`) — file rename where filename itself contains ` -> ` → ensure hook doesn't misclassify it
- `test_input_sanitizer_deeply_nested_missing_keys` — event with nested `tool_input` but no `file_path` key → hook exits 0

**Data Flow (representative — Gap 4 pattern):**
```python
@pytest.mark.parametrize("cmd,expected_exit", [
    ("rm -rf /", 2),
    ("git push --force origin dev", 2),
    ("git push origin feature-branch", 0),
])
def test_blocks_patterns(cmd, expected_exit, tmp_path):
    event = {"tool_name": "Bash", "tool_input": {"command": cmd}}
    result = subprocess.run(
        ["python3", str(HOOKS_DIR / "safety-check.py")],
        input=json.dumps(event),
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == expected_exit
```

**Edge Cases:**
- `evaluate()` direct import only works after the consolidate-utils-patterns item moves `BLOCKS` to utils. For now, use subprocess tests for BLOCKS patterns too — same pattern as above.
- `os.utime()` for staleness tests requires the snapshot directory to exist; set up in tmp_path fixture.
- The `git push --force-with-lease` case: `\b` in `--force\b` matches at the word/non-word boundary between `e` (word char) and `-` (non-word char), so `--force-with-lease` IS blocked by the existing pattern. Test asserts returncode == 2.

**Out of Scope:**
- Adding new safety BLOCKS patterns (separate backlog item if needed)
- Migrating tests from subprocess to import-based (covered by fix-coverage-measurement)
- Adding tests for hooks not listed above
- Integration tests (require live Claude session)
