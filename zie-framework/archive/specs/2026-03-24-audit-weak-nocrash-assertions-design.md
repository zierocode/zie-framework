---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-weak-nocrash-assertions.md
---

# Strengthen No-Crash Assertions to Verify Hook Side-Effects — Design Spec

**Problem:** Tests in `test_hooks_wip_checkpoint.py` (lines 121, 130) and similar patterns assert only `returncode == 0`, which passes even if the hook exited immediately via `sys.exit(0)` without performing any meaningful work.

**Approach:** For each test that currently asserts only `returncode == 0`, identify the expected observable side-effect of the code path under test and add a second assertion that verifies it. Side-effects include: counter file written with expected value, stdout containing a specific message, or (for network-path tests) stderr containing an error string from the attempted request. Tests that explicitly validate the "silent early exit" path (guardrails) are exempt — `returncode == 0` with `stdout == ""` is the correct and complete assertion there.

**Components:**
- `tests/unit/test_hooks_wip_checkpoint.py` — `TestWipCheckpointRoadmapEdgeCases`: `test_missing_roadmap_no_crash` (line 121), `test_empty_now_section_no_crash` (line 130), `test_malformed_now_items_graceful_skip` (line 139)
- `tests/unit/test_hooks_wip_checkpoint.py` — `TestWipCheckpointCounter`: `test_no_crash_on_fifth_edit_with_bad_url` (line 103)

**Data Flow — test cases to strengthen:**

1. `test_missing_roadmap_no_crash`: after `returncode == 0`, assert counter file exists and contains `"1"` — proves the hook reached counter logic before exiting due to empty `wip_summary`.
2. `test_empty_now_section_no_crash`: same as above — counter must be written even when `wip_summary` is empty, since the early exit is after counter increment.
3. `test_malformed_now_items_graceful_skip`: assert counter file written with `"1"` — the hook should increment and exit cleanly when no valid items are parsed.
4. `test_no_crash_on_fifth_edit_with_bad_url` (line 96-103): counter starts at `"4"`, after run assert counter file now contains `"5"` — proves hook reached network attempt and handled the error; also assert `r.stderr` contains the connection error string (not empty) since the hook prints the exception to stderr.

**Edge Cases:**
- Tests in `TestWipCheckpointGuardrails` (`test_no_action_without_api_key`, `test_no_action_for_non_edit_tool`) are intentionally silent-exit paths — do NOT add side-effect assertions; these are correct as-is.
- Counter path must be derived correctly (via `counter_path(tmp_path.name)`) to match what the hook writes — this is already done in the existing `_cleanup_counter` fixture.
- If a future hook version changes the early-exit order (e.g. increments counter after wip_summary check), tests must be updated accordingly — this spec reflects current hook logic in `wip-checkpoint.py`.

**Out of Scope:**
- Mocking the `urllib.request.urlopen` call (integration-style test — out of scope for unit layer).
- Adding side-effect assertions to `test_hooks_safety_check.py` (already asserts `BLOCKED` in stdout and exit code 2).
- Changing hook behaviour — only test assertions change.
