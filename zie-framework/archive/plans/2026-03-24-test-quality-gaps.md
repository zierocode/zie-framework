---
approved: true
approved_at: 2026-03-24
spec: specs/2026-03-24-test-quality-gaps-design.md
backlog: backlog/test-quality-gaps.md
---

# Test Quality: Fill Edge Case and Error Path Gaps — Implementation Plan

**Goal:** Add ~35 new test methods across 9 existing test files to cover seven gap categories: subprocess timeout error paths, JSON edge cases, None/empty event inputs, regex pattern unit tests, git-unavailable scenarios, time-boundary staleness tests, and file I/O argument validation. No hook code changes. No new test files.
**Architecture:** All tests use the existing subprocess invocation pattern — hooks called as child processes with crafted stdin JSON. Each task maps to one gap and targets specific test files.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_hooks_auto_test.py` | Gap 1: timeout test; Gap 2: empty config |
| Modify | `tests/unit/test_hooks_task_completed_gate.py` | Gap 1: timeout test |
| Modify | `tests/unit/test_hooks_safety_check.py` | Gap 4: parametrized BLOCKS + WARNS patterns |
| Modify | `tests/unit/test_input_sanitizer.py` | Gap 3: missing tool_name, empty command, malformed event; Gap 7: deeply nested missing keys |
| Modify | `tests/unit/test_hooks_sdlc_context.py` | Gap 6: staleness boundary at 299/300/301 seconds |
| Modify | `tests/unit/test_hooks_sdlc_compact.py` | Gap 5: git unavailable (PostCompact path) |
| Modify | `tests/unit/test_stop_guard.py` | Gap 7: rename arrow in filename |
| Modify | `tests/unit/test_hooks_wip_checkpoint.py` | Gap 7: zie-memory unreachable |
| Modify | `tests/unit/test_hooks_notification_log.py` | Gap 2: corrupt log with mixed valid/invalid lines |

---

## Task 1: Gap 1 — Subprocess timeout error paths

**Acceptance Criteria:**
- `auto-test.py` exits 0 when git hangs beyond the hook's internal timeout
- `task-completed-gate.py` exits 0 when git hangs beyond the hook's internal timeout
- Hook stdout is empty or valid JSON in both cases (no crash output)

**Files:**
- Modify: `tests/unit/test_hooks_auto_test.py`
- Modify: `tests/unit/test_hooks_task_completed_gate.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to class TestAutoTestGuardrails in test_hooks_auto_test.py

  def test_git_timeout_exits_zero(self, tmp_path):
      """auto-test.py must exit 0 when git hangs (TimeoutExpired caught by hook)."""
      import tempfile, stat
      # Create a fake git that sleeps forever
      bin_dir = tmp_path / "fakebin"
      bin_dir.mkdir()
      fake_git = bin_dir / "git"
      fake_git.write_text("#!/bin/sh\nsleep 60\n")
      fake_git.chmod(fake_git.stat().st_mode | stat.S_IEXEC)
      cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
      env = {
          **os.environ,
          "CLAUDE_CWD": str(cwd),
          "PATH": str(bin_dir) + ":" + os.environ.get("PATH", ""),
          "ZIE_MEMORY_API_KEY": "",
          "ZIE_AUTO_TEST_DEBOUNCE_MS": "0",
          "ZIE_TEST_RUNNER": "",
      }
      r = subprocess.run(
          [sys.executable, HOOK],
          input=json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}),
          capture_output=True, text=True, env=env, timeout=10,
      )
      assert r.returncode == 0
      assert "Traceback" not in r.stderr
  ```

  ```python
  # Append new class to test_hooks_task_completed_gate.py

  class TestGitTimeout:
      def test_git_timeout_exits_zero(self, tmp_path):
          """task-completed-gate.py must exit 0 when git hangs."""
          import stat
          bin_dir = tmp_path / "fakebin"
          bin_dir.mkdir()
          fake_git = bin_dir / "git"
          fake_git.write_text("#!/bin/sh\nsleep 60\n")
          fake_git.chmod(fake_git.stat().st_mode | stat.S_IEXEC)
          env = os.environ.copy()
          env["CLAUDE_CWD"] = str(tmp_path)
          env["PATH"] = str(bin_dir) + ":" + os.environ.get("PATH", "")
          event = {
              "tool_name": "TaskUpdate",
              "tool_input": {"id": "t1", "status": "completed", "title": "Implement feature X"},
          }
          r = subprocess.run(
              [sys.executable, HOOK],
              input=json.dumps(event),
              capture_output=True, text=True, env=env, timeout=10,
          )
          assert r.returncode == 0
          assert "Traceback" not in r.stderr
  ```

  Run: `make test-unit` — must FAIL if the hooks do not already catch `subprocess.TimeoutExpired`. If they do, tests pass on first run (gap was already covered); that is acceptable — the tests remain as regression guards.

---

- [ ] **Step 2: Verify (GREEN)**

  Run: `make test-unit` — both new tests must PASS (hooks already implement the two-tier error pattern which catches `TimeoutExpired` as `Exception`).

  If either test fails, the hook lacks a timeout guard — but this plan requires no hook code changes, so file a follow-up bug. The test itself is the deliverable.

---

- [ ] **Step 3: Refactor**

  Confirm no regressions in `TestAutoTestGuardrails` and `TestGitStatusCheck`.

  Run: `make test-unit` — full suite still PASS.

---

## Task 2: Gap 2 — JSON edge cases

**Acceptance Criteria:**
- `auto-test.py` exits 0 with empty `{}` config and emits no warning
- `notification-log.py` exits 0 when log file has one valid JSON line followed by one corrupt line, and recovers to a known-good state

**Note:** Several Gap 2 cases are already covered by existing tests:
- `test_corrupt_config_json` → covered by `TestAutoTestConfigParseWarning.test_warns_on_corrupt_config`
- `test_empty_lastfailed_dict` → covered by `TestPytestCacheCheck.test_empty_lastfailed_passes`
- `test_missing_lastfailed_file` → covered by `TestPytestCacheCheck.test_missing_cache_file_passes`
- `test_corrupt_wip_counter` → covered by `TestWipCheckpointCounter.test_corrupt_counter_file_resets_gracefully`
- `test_corrupt_notification_log` (all-corrupt) → covered by `TestPermissionPromptLogging.test_corrupted_log_resets_to_empty`

Two genuinely new cases remain: empty config in auto-test (the existing test checks for absent `.config`, not `{}`), and a mixed-content notification log.

**Files:**
- Modify: `tests/unit/test_hooks_auto_test.py`
- Modify: `tests/unit/test_hooks_notification_log.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to class TestAutoTestConfigParseWarning in test_hooks_auto_test.py

  def test_empty_config_json_exits_zero(self, tmp_path):
      """Empty {} config must exit 0, use all defaults, and emit no warning."""
      cwd = make_cwd(tmp_path, config={})
      r = run_hook(
          {"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
          tmp_cwd=cwd,
      )
      assert r.returncode == 0
      assert "[zie] warning" not in r.stderr
  ```

  ```python
  # Append new class to test_hooks_notification_log.py

  class TestCorruptLogMixedContent:
      def test_mixed_valid_corrupt_log_exits_zero(self, tmp_path):
          """Log with one valid JSON line + one corrupt line — hook exits 0 and recovers."""
          project = f"testproj-mixed-{tmp_path.name}"
          log = tmp_log_path("permission-log", project)
          # Write one valid record followed by one corrupt line
          log.write_text(
              '{"ts": "2026-01-01T00:00:00", "msg": "Read file /etc/hosts"}\n'
              "{bad json line\n"
          )
          r = run_hook(
              {"event": "Notification", "notification_type": "permission_prompt",
               "message": "some permission"},
              project,
          )
          assert r.returncode == 0
          # After recovery, log must be readable as valid JSON lines
          lines = [l for l in log.read_text().splitlines() if l.strip()]
          for line in lines:
              json.loads(line)  # must not raise
          log.unlink(missing_ok=True)
  ```

  Run: `make test-unit` — the empty-config test should PASS immediately (existing behavior). The mixed-corrupt-log test may PASS or FAIL depending on whether the hook already handles partial corruption.

---

- [ ] **Step 2: Verify (GREEN)**

  Run: `make test-unit` — both tests must PASS.

---

- [ ] **Step 3: Refactor**

  No cleanup required. Confirm no regressions in `TestAutoTestConfigParseWarning` and `TestPermissionPromptLogging`.

  Run: `make test-unit` — still PASS.

---

## Task 3: Gap 3 — None / empty event inputs

**Acceptance Criteria:**
- `safety-check.py` exits 0 when `tool_input` is `null`, `tool_name` is absent, `command` is `""`, or stdin is a non-dict JSON value
- `input-sanitizer.py` exits 0 for the same set of malformed inputs
- `stop-guard.py` exits 0 for the same set

**Note:** Several cases are already covered:
- `test_none_tool_input` in `test_input_sanitizer.py` — covered by `TestErrorResilience.test_none_tool_input_exits_zero`
- `test_empty_command` in `test_input_sanitizer.py` — covered by `TestBashConfirmRewrite.test_empty_command_exits_cleanly`
- `test_invalid_json_exits_zero` in `test_hooks_safety_check.py` — covered by `TestSafetyCheckPassThrough.test_invalid_json_exits_zero`

Genuinely new cases: `test_missing_tool_name` and `test_malformed_event_not_dict` for safety-check and stop-guard, and `test_missing_tool_name` for input-sanitizer.

**Files:**
- Modify: `tests/unit/test_hooks_safety_check.py`
- Modify: `tests/unit/test_input_sanitizer.py`
- Modify: `tests/unit/test_stop_guard.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to class TestSafetyCheckPassThrough in test_hooks_safety_check.py

  def test_missing_tool_name_exits_zero(self):
      """Event with no tool_name key must exit 0."""
      hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
      event = {"tool_input": {"command": "rm -rf /"}}
      r = subprocess.run([sys.executable, hook], input=json.dumps(event),
                        capture_output=True, text=True)
      assert r.returncode == 0

  def test_malformed_event_not_dict_exits_zero(self):
      """stdin containing a JSON string (not a dict) must exit 0."""
      hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
      r = subprocess.run([sys.executable, hook], input='"just a string"',
                        capture_output=True, text=True)
      assert r.returncode == 0

  def test_none_tool_input_exits_zero(self):
      """Event with tool_input: null must exit 0."""
      hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
      event = {"tool_name": "Bash", "tool_input": None}
      r = subprocess.run([sys.executable, hook], input=json.dumps(event),
                        capture_output=True, text=True)
      assert r.returncode == 0
  ```

  ```python
  # Append to class TestErrorResilience in test_input_sanitizer.py

  def test_missing_tool_name_exits_zero(self):
      """Event with no tool_name key must exit 0."""
      event = {"tool_input": {"file_path": "src/main.py"}}
      r = subprocess.run(
          [sys.executable, HOOK],
          input=json.dumps(event),
          capture_output=True, text=True,
      )
      assert r.returncode == 0
      assert r.stdout.strip() == ""

  def test_malformed_event_not_dict_exits_zero(self):
      """stdin containing a JSON string (not a dict) must exit 0."""
      r = subprocess.run(
          [sys.executable, HOOK],
          input='"just a string"',
          capture_output=True, text=True,
      )
      assert r.returncode == 0
      assert r.stdout.strip() == ""
  ```

  ```python
  # Append to class TestOuterGuard in test_stop_guard.py

  def test_missing_tool_name_exits_zero(self, tmp_path):
      """Event with no tool_name key must exit 0."""
      event = {"tool_input": {"command": "rm -rf /"}}
      r = run_hook(event, cwd=str(tmp_path))
      assert r.returncode == 0

  def test_malformed_event_not_dict_exits_zero(self, tmp_path):
      """stdin containing a JSON string (not a dict) must exit 0."""
      env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
      r = subprocess.run(
          [sys.executable, HOOK],
          input='"just a string"',
          capture_output=True, text=True, env=env,
      )
      assert r.returncode == 0
  ```

  Run: `make test-unit` — must FAIL for any hook that does not guard against non-dict inputs.

---

- [ ] **Step 2: Verify (GREEN)**

  Run: `make test-unit` — all new tests must PASS (the outer guard `except Exception -> sys.exit(0)` catches `AttributeError` from `.get()` on a non-dict).

---

- [ ] **Step 3: Refactor**

  Confirm no regressions in `TestSafetyCheckPassThrough`, `TestErrorResilience`, `TestOuterGuard`.

  Run: `make test-unit` — still PASS.

---

## Task 4: Gap 4 — Regex pattern unit tests for BLOCKS / WARNS

**Acceptance Criteria:**
- One `@pytest.mark.parametrize` covering all 12 BLOCKS patterns — each asserts `returncode == 2` and `"BLOCKED" in stdout`
- One `@pytest.mark.parametrize` covering both WARNS patterns — each asserts `returncode == 0` and `"WARNING" in stdout`
- `git push origin feature-branch` asserts `returncode == 0` (not blocked)
- `git push --force-with-lease` asserts `returncode == 2` (matches `--force\b` pattern)

**Note:** Individual BLOCKS cases are tested across `TestSafetyCheckBlocks` and `TestSafetyCheckRegexBypass`, but there is no single comprehensive parametrized sweep of all 12 canonical BLOCKS inputs or a parametrized WARNS sweep. These tests are additive — they document the full contract in one place.

**Files:**
- Modify: `tests/unit/test_hooks_safety_check.py`

---

- [ ] **Step 1: Write tests (RED — or already GREEN for most entries)**

  ```python
  # Append new class to test_hooks_safety_check.py

  class TestSafetyCheckPatternCoverage:
      """Parametrized sweep of all canonical BLOCKS and WARNS patterns.

      These tests confirm the current safety-check.py pattern set. If a test
      passes on first run, the existing behavior is already correct — the test
      remains as a regression guard. If it fails, the hook has a gap.
      """

      @pytest.mark.parametrize("cmd", [
          "rm -rf /",
          "rm -rf ~",
          "rm -rf .",
          "DROP DATABASE mydb",
          "DROP TABLE users",
          "TRUNCATE TABLE events",
          "git push --force",
          "git push -f origin dev",
          "git push origin main",
          "git push origin master",
          "git reset --hard HEAD~1",
          "git commit --no-verify -m skip",
      ])
      def test_blocks_pattern_exits_2(self, cmd):
          """Each canonical BLOCKS command must return exit code 2."""
          r = run_hook("Bash", cmd)
          assert r.returncode == 2, (
              f"Expected returncode 2 for BLOCKS command {cmd!r}, got {r.returncode}"
          )
          assert "BLOCKED" in r.stdout, (
              f"Expected 'BLOCKED' in stdout for command {cmd!r}"
          )

      @pytest.mark.parametrize("cmd", [
          "docker compose down --volumes",
          "alembic downgrade base",
      ])
      def test_warns_pattern_exits_0_with_warning(self, cmd):
          """Each canonical WARNS command must return exit code 0 with WARNING in stdout."""
          r = run_hook("Bash", cmd)
          assert r.returncode == 0, (
              f"Expected returncode 0 for WARNS command {cmd!r}, got {r.returncode}"
          )
          assert "WARNING" in r.stdout, (
              f"Expected 'WARNING' in stdout for command {cmd!r}"
          )

      def test_feature_branch_push_not_blocked(self):
          """git push to a non-protected branch must not be blocked."""
          r = run_hook("Bash", "git push origin feature-branch")
          assert r.returncode == 0, (
              "git push origin feature-branch must not be blocked"
          )

      def test_force_with_lease_is_blocked_by_force_pattern(self):
          """--force-with-lease matches --force\\b because '-' is a non-word char.

          The \\b boundary in --force\\b matches between 'e' (word char) and '-'
          (non-word char), so --force-with-lease IS caught by the BLOCKS pattern.
          """
          r = run_hook("Bash", "git push --force-with-lease origin dev")
          assert r.returncode == 2, (
              "git push --force-with-lease must be blocked by --force\\b pattern"
          )
          assert "BLOCKED" in r.stdout
  ```

  Run: `make test-unit` — most parametrized cases will PASS immediately (existing behavior). Any failure identifies a real gap in the pattern set.

---

- [ ] **Step 2: Verify (GREEN)**

  Run: `make test-unit` — all parametrized cases must PASS.

  If `DROP TABLE users` or `TRUNCATE TABLE events` fail, check whether the hook's pattern uses `\btable\b` or a more specific form. Adjust the test command to match the actual pattern as documented in the hook source.

---

- [ ] **Step 3: Refactor**

  Remove any `TestSafetyCheckBlocks` individual tests that are now fully duplicated by the parametrized set — only if they add no extra assertion (e.g., checking `r.stderr`). Keep tests that assert additional properties beyond returncode + "BLOCKED".

  Run: `make test-unit` — still PASS.

---

## Task 5: Gap 5 — Git unavailable

**Acceptance Criteria:**
- `sdlc-compact.py` PostCompact path exits 0 when git is unavailable (snapshot read path, not write path)
- `stop-guard.py` exits 0 when git is unavailable (already covered — verify no regression)

**Note:** Both hooks already have git-unavailable tests:
- `test_hooks_sdlc_compact.py`: `TestSdlcCompactPreCompact.test_git_unavailable_writes_snapshot_with_empty_git_fields` covers PreCompact
- `test_stop_guard.py`: `TestGitErrorResilience.test_exits_zero_when_git_not_on_path` covers stop-guard

The genuine gap is the **PostCompact** path in sdlc-compact, which reads a snapshot and calls git for live fallback — not yet tested under git-unavailable conditions.

**Files:**
- Modify: `tests/unit/test_hooks_sdlc_compact.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to class TestSdlcCompactPostCompact in test_hooks_sdlc_compact.py

  def test_postcompact_git_unavailable_exits_zero(self, tmp_path):
      """PostCompact must exit 0 even when git is not on PATH."""
      cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
      # No snapshot — forces live fallback which calls git
      assert not snapshot_path(tmp_path).exists()
      empty_bin = tmp_path / "empty_bin"
      empty_bin.mkdir()
      r = run_hook(
          "PostCompact",
          tmp_cwd=cwd,
          env_overrides={"PATH": str(empty_bin)},
      )
      assert r.returncode == 0
      assert "Traceback" not in r.stderr
  ```

  Run: `make test-unit` — must FAIL if PostCompact does not guard git calls.

---

- [ ] **Step 2: Verify (GREEN)**

  Run: `make test-unit` — new test must PASS.

---

- [ ] **Step 3: Refactor**

  Confirm existing PreCompact git-unavailable test still passes.

  Run: `make test-unit` — still PASS.

---

## Task 6: Gap 6 — Time-boundary staleness test

**Acceptance Criteria:**
- File with mtime 299 seconds ago → context reports `tests: recent` (not stale)
- File with mtime 300 seconds ago → behavior matches the hook's boundary condition (`<` vs `<=`)
- File with mtime 301 seconds ago → context reports `tests: stale`

**Files:**
- Modify: `tests/unit/test_hooks_sdlc_context.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append new class to test_hooks_sdlc_context.py

  class TestSdlcContextStalenessBoundary:
      """STALE_THRESHOLD_SECS=300 boundary tests using os.utime()."""

      @pytest.fixture(autouse=True)
      def _cleanup(self, tmp_path):
          yield
          f = project_tmp_path("last-test", tmp_path.name)
          if f.exists():
              f.unlink()

      def _run_with_mtime(self, tmp_path, age_secs):
          """Write a last-test file, set its mtime to age_secs ago, run the hook."""
          import time as _time
          cwd = make_cwd(tmp_path, roadmap=ROADMAP_WITH_IMPLEMENT)
          tmp_file = project_tmp_path("last-test", tmp_path.name)
          tmp_file.write_text("ok")
          old_time = _time.time() - age_secs
          os.utime(tmp_file, (old_time, old_time))
          return run_hook({"prompt": "hello"}, tmp_cwd=cwd)

      def test_299_seconds_ago_is_recent(self, tmp_path):
          """File 299 seconds old must report tests: recent (below threshold)."""
          r = self._run_with_mtime(tmp_path, 299)
          ctx = parse_context(r)
          assert "tests: recent" in ctx, (
              f"Expected 'tests: recent' for 299s-old file, got: {ctx!r}"
          )

      def test_301_seconds_ago_is_stale(self, tmp_path):
          """File 301 seconds old must report tests: stale (above threshold)."""
          r = self._run_with_mtime(tmp_path, 301)
          ctx = parse_context(r)
          assert "tests: stale" in ctx, (
              f"Expected 'tests: stale' for 301s-old file, got: {ctx!r}"
          )

      def test_300_seconds_ago_boundary(self, tmp_path):
          """File exactly 300 seconds old — verify result matches hook's boundary operator.

          The hook uses elapsed >= STALE_THRESHOLD_SECS (i.e., >= 300), so a file
          exactly 300 seconds old IS considered stale. This test documents the
          chosen boundary behavior. If the operator changes, this test will fail
          as an intentional regression signal.
          """
          r = self._run_with_mtime(tmp_path, 300)
          ctx = parse_context(r)
          # >= 300 means 300s old → stale
          assert "tests: stale" in ctx, (
              f"Expected 'tests: stale' at exactly 300s boundary, got: {ctx!r}. "
              "If the hook uses '>' instead of '>=', update this assertion to 'tests: recent'."
          )
  ```

  Run: `make test-unit` — `test_299_seconds_ago_is_recent` and `test_301_seconds_ago_is_stale` should PASS (these verify clearly separated behavior). `test_300_seconds_ago_boundary` may FAIL if the hook's boundary operator differs from the comment's assumption — this is intentional.

---

- [ ] **Step 2: Verify (GREEN)**

  Check the hook source to confirm the boundary operator (`>=` or `>`). Adjust the boundary test assertion to match.

  Run: `make test-unit` — all three boundary tests must PASS.

---

- [ ] **Step 3: Refactor**

  Confirm existing `test_tests_stale_when_tmp_file_old` (400 seconds) still PASS.

  Run: `make test-unit` — still PASS.

---

## Task 7: Gap 7 — File I/O and argument validation

**Acceptance Criteria:**
- `wip-checkpoint.py` exits 0 when `ZIE_MEMORY_API_URL` points to `http://localhost:19999` (non-https is blocked before any network call — already exits 0 via URL guard)
- `stop-guard.py` exits 0 and does not misclassify a rename where the filename itself contains ` -> `
- `input-sanitizer.py` exits 0 when event has nested `tool_input` with no `file_path` key

**Note:** The wip-checkpoint memory-unreachable case is already covered by `TestWipCheckpointCounter.test_no_crash_on_fifth_edit_with_bad_url` (https URL, bad host) and `TestWipCheckpointUrlSafety.test_exits_zero_with_http_scheme_url` (http URL blocked by guard). The http://localhost:19999 variant specifically tests the URL safety guard, which is already confirmed. The genuinely new cases are the stop-guard arrow-in-filename and the input-sanitizer nested missing keys.

**Files:**
- Modify: `tests/unit/test_hooks_wip_checkpoint.py`
- Modify: `tests/unit/test_stop_guard.py`
- Modify: `tests/unit/test_input_sanitizer.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to class TestWipCheckpointUrlSafety in test_hooks_wip_checkpoint.py

  def test_memory_unreachable_http_url_exits_zero(self, tmp_path):
      """http://localhost:19999 (nothing listening) — URL guard blocks before network call."""
      zf = tmp_path / "zie-framework"
      zf.mkdir()
      env = {
          **os.environ,
          "CLAUDE_CWD": str(tmp_path),
          "ZIE_MEMORY_API_KEY": "testkey",
          "ZIE_MEMORY_API_URL": "http://localhost:19999",
      }
      r = subprocess.run(
          [sys.executable, HOOK],
          input=json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}}),
          capture_output=True, text=True, env=env,
      )
      assert r.returncode == 0
      assert "Traceback" not in r.stderr
  ```

  ```python
  # Append new class to test_stop_guard.py

  class TestRenameArrowInFilename:
      """stop-guard parses git status output which uses ' -> ' for renames.
      If a filename itself contains ' -> ', the parser must not misclassify it.
      """

      def _init_repo(self, tmp_path):
          subprocess.run(["git", "init"], cwd=str(tmp_path), check=True,
                         capture_output=True)
          subprocess.run(
              ["git", "commit", "--allow-empty", "-m", "init"],
              cwd=str(tmp_path), check=True, capture_output=True,
              env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.com",
                   "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.com"},
          )

      def test_arrow_in_filename_does_not_crash(self, tmp_path):
          """A file whose name contains ' -> ' must not cause the hook to crash or misclassify."""
          self._init_repo(tmp_path)
          hooks_dir = tmp_path / "hooks"
          hooks_dir.mkdir()
          # Create a file with ' -> ' in its name
          arrow_file = hooks_dir / "old -> new.py"
          arrow_file.write_text("# arrow in filename\n")
          r = run_hook({}, cwd=str(tmp_path))
          assert r.returncode == 0
          assert "Traceback" not in r.stderr
  ```

  ```python
  # Append to class TestErrorResilience in test_input_sanitizer.py

  def test_deeply_nested_tool_input_missing_file_path_exits_zero(self, tmp_path):
      """Nested tool_input dict without file_path key must exit 0 without crash."""
      event = {
          "tool_name": "Write",
          "tool_input": {
              "nested": {"deeply": {"no_file_path": True}},
              "content": "some content",
          },
      }
      r = subprocess.run(
          [sys.executable, HOOK],
          input=json.dumps(event),
          capture_output=True, text=True,
          env={**os.environ, "CLAUDE_CWD": str(tmp_path)},
      )
      assert r.returncode == 0
      assert r.stdout.strip() == ""
  ```

  Run: `make test-unit` — the wip-checkpoint and input-sanitizer tests should PASS immediately (existing guards cover them). The stop-guard arrow-in-filename test may FAIL if the parser does a naive split on ` -> `.

---

- [ ] **Step 2: Verify (GREEN)**

  Run: `make test-unit` — all three tests must PASS.

---

- [ ] **Step 3: Refactor**

  Confirm no regressions in `TestWipCheckpointUrlSafety`, `TestGitErrorResilience`, `TestErrorResilience`.

  Run: `make test-unit` — still PASS.

---

**Commit:** `git add tests/unit/ && git commit -m "test: test-quality-gaps — fill edge case and error path gaps across 9 test files"`
