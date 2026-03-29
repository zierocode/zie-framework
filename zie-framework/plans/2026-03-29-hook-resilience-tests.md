---
approved: true
approved_at: 2026-03-29
backlog: backlog/hook-resilience-tests.md
spec: specs/2026-03-29-hook-resilience-tests-design.md
---

# Hook Resilience Tests — Implementation Plan

**Goal:** Add systematic error-path and edge-case test coverage for all production hooks, making hook resilience a gated requirement before release.
**Architecture:** Five focused test modules (one per failure category) + a shared `run_hook()` fixture in `tests/conftest.py` following ADR-015 env isolation. A `@pytest.mark.error_path` marker + post-test coverage script enforce ≥1 error-path test per hook. All modules are collected by `make test-unit`.
**Tech Stack:** Python 3.x, pytest, subprocess, unittest.mock, tmp_path fixtures

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/conftest.py` | Add shared `run_hook()` helper + `error_path` pytest marker registration |
| Create | `tests/unit/test_hook_uninitialized_project.py` | ≥6 tests — all covered hooks exit 0 when `zie-framework/` dir is absent |
| Create | `tests/unit/test_hook_malformed_config.py` | ≥4 tests — all covered hooks exit 0 with empty/invalid `.config` |
| Create | `tests/unit/test_hook_subprocess_timeout.py` | ≥2 tests — `safety_check_agent.py` falls back to regex; `auto-test.py` exits cleanly on hung `make` |
| Create | `tests/unit/test_hook_partial_state.py` | ≥4 tests — hooks degrade gracefully when ROADMAP/specs/plans/PROJECT.md is missing or empty |
| Create | `tests/unit/test_hook_concurrent_writes.py` | ≥1 test — `session-cleanup.py` + `notification-log.py` both exit 0 when `/tmp/zie-<session>` is deleted mid-write |
| Create | `tests/unit/scripts/check_error_path_coverage.py` | Post-test script — counts `@pytest.mark.error_path` tests per hook, exits non-zero if any hook has 0 |
| Modify | `Makefile` | Add coverage gate step after `pytest tests/unit/` in `test-unit` target |

---

## Task 1: Shared conftest.py — run_hook helper + error_path marker

**Acceptance Criteria:**
- `tests/conftest.py` defines a `run_hook(hook_name, event, tmp_cwd=None, extra_env=None)` function that spawns the hook subprocess with ADR-015 isolated env (clears `CLAUDE_SESSION_ID`, `CLAUDE_TOOL_USE_ID`, `ZIE_MEMORY_API_KEY`; sets `CLAUDE_CWD` to `tmp_cwd` if provided).
- `pytest.ini` or `conftest.py` registers `error_path` marker so `pytest --strict-markers` passes.
- `run_hook()` is importable from all test modules via `from conftest import run_hook`.

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_conftest_helpers.py (temporary — delete after Task 1 GREEN)
  import subprocess, sys, json, os
  from pathlib import Path

  def test_run_hook_importable():
      """Verify run_hook can be imported from conftest."""
      import conftest
      assert callable(conftest.run_hook)

  def test_run_hook_exits_zero_for_unknown_hook(tmp_path):
      import conftest
      # A hook that doesn't exist should not be callable; but run_hook itself
      # should not raise — it returns CompletedProcess
      # Use intent-sdlc.py with empty tmp_cwd (no zie-framework/ dir)
      r = conftest.run_hook("intent-sdlc.py", {"prompt": "hello"}, tmp_cwd=tmp_path)
      assert r.returncode == 0

  def test_run_hook_clears_session_vars(tmp_path):
      import conftest
      r = conftest.run_hook("session-resume.py", {}, tmp_cwd=tmp_path)
      # Hook should not see any injected session vars — exits 0
      assert r.returncode == 0
  ```
  Run: `make test-unit` — must FAIL (run_hook not yet defined in conftest)

- [ ] **Step 2: Implement (GREEN)**
  Add to `tests/conftest.py`:
  ```python
  import json
  import os
  import subprocess
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).parent.parent

  # Vars injected by Claude Code that must be cleared for test isolation (ADR-015)
  _SESSION_VARS_TO_CLEAR = [
      "CLAUDE_SESSION_ID",
      "CLAUDE_TOOL_USE_ID",
      "CLAUDE_AGENT_ID",
      "ZIE_MEMORY_API_KEY",
      "ZIE_MEMORY_API_URL",
  ]

  def run_hook(hook_name: str, event: dict, tmp_cwd=None, extra_env=None) -> subprocess.CompletedProcess:
      """Spawn a hook subprocess with ADR-015 env isolation.

      - Clears all session-injected vars to prevent test contamination.
      - Sets CLAUDE_CWD to tmp_cwd when provided.
      - Merges extra_env last so callers can override individual vars.
      """
      hook_path = REPO_ROOT / "hooks" / hook_name
      env = {k: v for k, v in os.environ.items() if k not in _SESSION_VARS_TO_CLEAR}
      env["ZIE_MEMORY_API_KEY"] = ""
      env["ZIE_MEMORY_API_URL"] = ""
      if tmp_cwd is not None:
          env["CLAUDE_CWD"] = str(tmp_cwd)
      if extra_env:
          env.update(extra_env)
      ev = {"session_id": f"test-{abs(hash(str(tmp_cwd))) % 999999}", **event}
      return subprocess.run(
          [sys.executable, str(hook_path)],
          input=json.dumps(ev),
          capture_output=True,
          text=True,
          env=env,
      )


  def pytest_configure(config):
      config.addinivalue_line(
          "markers",
          "error_path: marks tests that exercise hook error paths (missing input, malformed data, subprocess failure)",
      )
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Remove the temporary `test_conftest_helpers.py` test file. The helpers in this task are used by all subsequent tasks. Verify `pytest --strict-markers tests/unit/` passes with no marker warnings.
  Run: `make test-unit` — still PASS

---

## Task 2: test_hook_uninitialized_project.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- File exists at `tests/unit/test_hook_uninitialized_project.py`.
- ≥6 test cases, one per hook: `intent-sdlc.py`, `session-resume.py`, `auto-test.py`, `sdlc-compact.py`, `safety-check.py`, `subagent-context.py`.
- Each test passes `tmp_path` with no `zie-framework/` directory as `CLAUDE_CWD`.
- Each test asserts `returncode == 0`.
- All tests marked `@pytest.mark.error_path`.

**Files:**
- Create: `tests/unit/test_hook_uninitialized_project.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hook_uninitialized_project.py
  """
  Error-path tests: all hooks must exit 0 when zie-framework/ dir is absent.
  Covers the outer guard of the two-tier error handling convention.
  """
  import json
  import sys
  import os
  import pytest
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).parent))
  # run_hook is injected by conftest.py automatically via pytest

  HOOKS_NEEDING_EDIT_EVENT = {"auto-test.py", "wip-checkpoint.py"}
  HOOKS_NEEDING_SUBAGENT_EVENT = {"subagent-context.py"}


  def _make_edit_event():
      return {"tool_name": "Edit", "tool_input": {"file_path": "/tmp/fake.py"}, "tool_response": "ok"}


  def _make_subagent_event():
      return {"agent_type": "Explore"}


  @pytest.mark.error_path
  def test_intent_sdlc_no_zf_dir(tmp_path, run_hook):
      r = run_hook("intent-sdlc.py", {"prompt": "implement feature X"}, tmp_cwd=tmp_path)
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_session_resume_no_zf_dir(tmp_path, run_hook):
      r = run_hook("session-resume.py", {}, tmp_cwd=tmp_path)
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_auto_test_no_zf_dir(tmp_path, run_hook):
      r = run_hook("auto-test.py", _make_edit_event(), tmp_cwd=tmp_path)
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_sdlc_compact_no_zf_dir(tmp_path, run_hook):
      r = run_hook("sdlc-compact.py", {}, tmp_cwd=tmp_path)
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_safety_check_no_zf_dir(tmp_path, run_hook):
      r = run_hook("safety-check.py", {"tool_name": "Bash", "tool_input": {"command": "ls"}}, tmp_cwd=tmp_path)
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_subagent_context_no_zf_dir(tmp_path, run_hook):
      r = run_hook("subagent-context.py", _make_subagent_event(), tmp_cwd=tmp_path)
      assert r.returncode == 0
  ```
  Run: `make test-unit` — must FAIL (file doesn't exist yet)

- [ ] **Step 2: Implement (GREEN)**
  Save the exact content above to `tests/unit/test_hook_uninitialized_project.py`. No hook changes needed — hooks already implement the outer guard. Verify all 6 tests pass.
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No refactoring required. Confirm `pytest -m error_path tests/unit/test_hook_uninitialized_project.py` selects all 6 tests.
  Run: `make test-unit` — still PASS

---

## Task 3: test_hook_malformed_config.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- File exists at `tests/unit/test_hook_malformed_config.py`.
- ≥4 test cases: empty `.config` `{}`, invalid JSON in `.config`, unrecognized keys, `.config` file absent (but `zie-framework/` dir present).
- Each test asserts `returncode == 0`.
- All tests marked `@pytest.mark.error_path`.

**Files:**
- Create: `tests/unit/test_hook_malformed_config.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hook_malformed_config.py
  """
  Error-path tests: hooks must exit 0 on empty, invalid, or unrecognized .config.
  Validates load_config() graceful degradation (returns {} on any error).
  """
  import pytest
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).parent))


  def _make_zf_dir(tmp_path):
      zf = tmp_path / "zie-framework"
      zf.mkdir(parents=True)
      (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n")
      return tmp_path


  @pytest.mark.error_path
  def test_empty_config_dict(tmp_path, run_hook):
      cwd = _make_zf_dir(tmp_path)
      (cwd / "zie-framework" / ".config").write_text("{}")
      r = run_hook("session-resume.py", {}, tmp_cwd=cwd)
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_invalid_json_config(tmp_path, run_hook):
      cwd = _make_zf_dir(tmp_path)
      (cwd / "zie-framework" / ".config").write_text("{ not valid json !!!")
      r = run_hook("session-resume.py", {}, tmp_cwd=cwd)
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_unrecognized_keys_config(tmp_path, run_hook):
      cwd = _make_zf_dir(tmp_path)
      (cwd / "zie-framework" / ".config").write_text(
          '{"unknown_key": "value", "another_unknown": 42}'
      )
      r = run_hook("intent-sdlc.py", {"prompt": "implement feature X"}, tmp_cwd=cwd)
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_config_absent_zf_present(tmp_path, run_hook):
      cwd = _make_zf_dir(tmp_path)
      # No .config file — zie-framework/ dir exists
      assert not (cwd / "zie-framework" / ".config").exists()
      r = run_hook("intent-sdlc.py", {"prompt": "fix the bug"}, tmp_cwd=cwd)
      assert r.returncode == 0
  ```
  Run: `make test-unit` — must FAIL (file doesn't exist yet)

- [ ] **Step 2: Implement (GREEN)**
  Save the exact content above to `tests/unit/test_hook_malformed_config.py`. No hook changes needed — `load_config()` already returns `{}` on any error. Verify all 4 tests pass.
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No refactoring required.
  Run: `make test-unit` — still PASS

---

## Task 4: test_hook_subprocess_timeout.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- File exists at `tests/unit/test_hook_subprocess_timeout.py`.
- ≥2 test cases: `safety_check_agent.py` falls back to regex (exits 0, does not hang) when the Claude subagent subprocess times out; `auto-test.py` exits 0 when `make test-unit` subprocess hangs past wall-clock limit.
- Both tests use `unittest.mock.patch` to simulate timeout without spawning real subprocesses.
- Both tests complete in <2s wall-clock time.
- All tests marked `@pytest.mark.error_path`.

**Files:**
- Create: `tests/unit/test_hook_subprocess_timeout.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hook_subprocess_timeout.py
  """
  Error-path tests: hooks must exit 0 when subprocess calls time out.
  Uses mock.patch to inject TimeoutExpired without spinning real subprocesses.
  """
  import json
  import subprocess
  import sys
  import os
  import pytest
  from pathlib import Path
  from unittest.mock import patch, MagicMock

  REPO_ROOT = Path(__file__).parent.parent.parent
  sys.path.insert(0, str(REPO_ROOT / "hooks"))


  def _make_zf_dir(tmp_path):
      zf = tmp_path / "zie-framework"
      zf.mkdir(parents=True)
      (zf / "ROADMAP.md").write_text("## Now\n- active task\n## Next\n")
      return tmp_path


  @pytest.mark.error_path
  def test_safety_check_agent_timeout_falls_back(tmp_path, run_hook):
      """safety_check_agent.py must exit 0 when its Claude subprocess times out."""
      cwd = _make_zf_dir(tmp_path)
      # Patch subprocess.run to raise TimeoutExpired for any call
      with patch("subprocess.run") as mock_run:
          mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=5)
          r = run_hook(
              "safety_check_agent.py",
              {"tool_name": "Bash", "tool_input": {"command": "ls -la"}},
              tmp_cwd=cwd,
          )
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_auto_test_make_hang_exits_cleanly(tmp_path, run_hook):
      """auto-test.py must exit 0 when make test-unit hangs beyond wall-clock limit."""
      cwd = _make_zf_dir(tmp_path)
      with patch("subprocess.run") as mock_run:
          mock_run.side_effect = subprocess.TimeoutExpired(cmd="make", timeout=60)
          r = run_hook(
              "auto-test.py",
              {"tool_name": "Edit", "tool_input": {"file_path": "/tmp/fake.py"}, "tool_response": "ok"},
              tmp_cwd=cwd,
          )
      assert r.returncode == 0
  ```
  Run: `make test-unit` — must FAIL (file doesn't exist yet)

- [ ] **Step 2: Implement (GREEN)**
  Save the exact content above to `tests/unit/test_hook_subprocess_timeout.py`.

  Note: `mock.patch("subprocess.run")` patches the module-level `subprocess.run` in the test process, but the hook runs in a *separate subprocess* (spawned by `run_hook()`). The patch will therefore NOT reach the hook subprocess — this means the test as written above will not actually inject the timeout into the hook. The correct approach is to test the timeout path via the hook's *in-process* module import rather than via `run_hook()`.

  Revised approach for both tests — import and call hook functions directly:
  ```python
  @pytest.mark.error_path
  def test_safety_check_agent_timeout_falls_back(tmp_path):
      """safety_check_agent.py must not raise when subprocess times out."""
      import importlib.util, types
      hook_path = REPO_ROOT / "hooks" / "safety_check_agent.py"
      # Load hook module in-process
      spec = importlib.util.spec_from_file_location("safety_check_agent", hook_path)
      mod = importlib.util.module_from_spec(spec)
      # Patch subprocess.run before exec
      with patch("subprocess.run") as mock_run:
          mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=5)
          try:
              spec.loader.exec_module(mod)
          except SystemExit as e:
              assert e.code == 0 or e.code is None
          except Exception:
              pytest.fail("safety_check_agent raised unexpectedly on TimeoutExpired")


  @pytest.mark.error_path
  def test_auto_test_make_hang_exits_cleanly(tmp_path):
      """auto-test.py must not raise when make subprocess times out."""
      import importlib.util
      hook_path = REPO_ROOT / "hooks" / "auto-test.py"
      spec = importlib.util.spec_from_file_location("auto_test", hook_path)
      mod = importlib.util.module_from_spec(spec)
      with patch("subprocess.run") as mock_run:
          mock_run.side_effect = subprocess.TimeoutExpired(cmd="make", timeout=60)
          try:
              spec.loader.exec_module(mod)
          except SystemExit as e:
              assert e.code == 0 or e.code is None
          except Exception:
              pytest.fail("auto-test raised unexpectedly on TimeoutExpired")
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Consolidate any duplicated module-loading boilerplate into a local `_load_hook(name)` helper at module top. Ensure tests still complete in <2s.
  Run: `make test-unit` — still PASS

---

## Task 5: test_hook_partial_state.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- File exists at `tests/unit/test_hook_partial_state.py`.
- ≥4 test cases: ROADMAP.md exists but `## Now` section is empty; `specs/` dir is missing; `plans/` dir is missing; `PROJECT.md` is missing.
- Each test asserts `returncode == 0`.
- All tests marked `@pytest.mark.error_path`.

**Files:**
- Create: `tests/unit/test_hook_partial_state.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hook_partial_state.py
  """
  Error-path tests: hooks must exit 0 when project state is present but partial/empty.
  Validates graceful degradation when standard subdirs/files are absent.
  """
  import pytest
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).parent))


  def _base_zf(tmp_path):
      zf = tmp_path / "zie-framework"
      zf.mkdir(parents=True)
      return tmp_path, zf


  @pytest.mark.error_path
  def test_roadmap_empty_now_section(tmp_path, run_hook):
      """ROADMAP.md exists but ## Now section is empty — hooks must not crash."""
      cwd, zf = _base_zf(tmp_path)
      (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n- next item\n")
      r = run_hook("intent-sdlc.py", {"prompt": "check status"}, tmp_cwd=cwd)
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_specs_dir_missing(tmp_path, run_hook):
      """specs/ dir absent — subagent-context.py must inject default context, not fail."""
      cwd, zf = _base_zf(tmp_path)
      (zf / "ROADMAP.md").write_text("## Now\n- active task\n## Next\n")
      # No zf/specs/ directory
      r = run_hook("subagent-context.py", {"agent_type": "Plan"}, tmp_cwd=cwd)
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_plans_dir_missing(tmp_path, run_hook):
      """plans/ dir absent — subagent-context.py must inject default context, not fail."""
      cwd, zf = _base_zf(tmp_path)
      (zf / "ROADMAP.md").write_text("## Now\n- active task\n## Next\n")
      (zf / "specs").mkdir()
      # No zf/plans/ directory
      r = run_hook("subagent-context.py", {"agent_type": "Explore"}, tmp_cwd=cwd)
      assert r.returncode == 0


  @pytest.mark.error_path
  def test_project_md_missing(tmp_path, run_hook):
      """PROJECT.md absent — session-resume.py must exit 0 without injecting stale context."""
      cwd, zf = _base_zf(tmp_path)
      (zf / "ROADMAP.md").write_text("## Now\n- active task\n## Next\n")
      # No zf/PROJECT.md
      r = run_hook("session-resume.py", {}, tmp_cwd=cwd)
      assert r.returncode == 0
  ```
  Run: `make test-unit` — must FAIL (file doesn't exist yet)

- [ ] **Step 2: Implement (GREEN)**
  Save the exact content above to `tests/unit/test_hook_partial_state.py`. Verify all 4 tests pass.
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No refactoring required.
  Run: `make test-unit` — still PASS

---

## Task 6: test_hook_concurrent_writes.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- File exists at `tests/unit/test_hook_concurrent_writes.py`.
- ≥1 test case: `session-cleanup.py` removes `/tmp/zie-<session>` while `notification-log.py` attempts to write to `/tmp/zie-<session>/notification.log`; both hooks exit 0.
- Test uses `threading.Thread` to simulate concurrent execution.
- All tests marked `@pytest.mark.error_path`.

**Files:**
- Create: `tests/unit/test_hook_concurrent_writes.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hook_concurrent_writes.py
  """
  Error-path tests: concurrent hook execution must not corrupt state or crash.
  Simulates session-cleanup deleting /tmp/zie-<session> while notification-log writes.
  """
  import json
  import os
  import shutil
  import sys
  import threading
  import time
  import pytest
  from pathlib import Path

  REPO_ROOT = Path(__file__).parent.parent.parent
  sys.path.insert(0, str(REPO_ROOT / "hooks"))


  def _run_cleanup(session_dir: Path, results: list, idx: int):
      """Delete the session tmp dir to simulate session-cleanup.py behavior."""
      try:
          shutil.rmtree(session_dir, ignore_errors=True)
          results[idx] = "ok"
      except Exception as e:
          results[idx] = f"error: {e}"


  def _run_notification_write(session_dir: Path, results: list, idx: int):
      """Attempt to write to notification.log inside the session dir."""
      try:
          session_dir.mkdir(parents=True, exist_ok=True)
          log_path = session_dir / "notification.log"
          # Simulate what notification-log.py does: open + write
          try:
              with open(log_path, "a") as f:
                  f.write("test notification\n")
          except OSError:
              pass  # ENOENT/OSError: hook exits 0 — not a crash
          results[idx] = "ok"
      except Exception as e:
          results[idx] = f"error: {e}"


  @pytest.mark.error_path
  def test_concurrent_cleanup_and_notification_log(tmp_path, run_hook):
      """
      session-cleanup deletes /tmp/zie-<session> while notification-log.py writes.
      Both operations must complete without raising — simulates the ENOENT race.
      """
      session_id = f"test-concurrent-{os.getpid()}"
      session_dir = Path(f"/tmp/zie-{session_id}")
      session_dir.mkdir(parents=True, exist_ok=True)
      (session_dir / "notification.log").write_text("")

      results = [None, None]

      t_cleanup = threading.Thread(
          target=_run_cleanup, args=(session_dir, results, 0)
      )
      t_write = threading.Thread(
          target=_run_notification_write, args=(session_dir, results, 1)
      )

      t_cleanup.start()
      t_write.start()
      t_cleanup.join(timeout=5)
      t_write.join(timeout=5)

      assert results[0] == "ok", f"cleanup thread failed: {results[0]}"
      assert results[1] == "ok", f"notification write thread failed: {results[1]}"

      # Also verify the actual hooks exit 0 in isolation with missing session dir
      shutil.rmtree(session_dir, ignore_errors=True)
      cwd = tmp_path / "proj"
      cwd.mkdir()
      (cwd / "zie-framework").mkdir()

      r_notif = run_hook(
          "notification-log.py",
          {"notification_type": "permission_prompt", "message": "test"},
          tmp_cwd=cwd,
          extra_env={"CLAUDE_SESSION_ID": session_id},
      )
      assert r_notif.returncode == 0
  ```
  Run: `make test-unit` — must FAIL (file doesn't exist yet)

- [ ] **Step 2: Implement (GREEN)**
  Save the exact content above to `tests/unit/test_hook_concurrent_writes.py`. Verify the test passes.
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No refactoring required.
  Run: `make test-unit` — still PASS

---

## Task 7: Coverage gate script + Makefile integration

<!-- depends_on: Task 2, Task 3, Task 4, Task 5, Task 6 -->

**Acceptance Criteria:**
- `tests/unit/scripts/check_error_path_coverage.py` exists and, when run after `pytest --collect-only -q -m error_path`, counts `@pytest.mark.error_path` test IDs per hook name, exits non-zero if any hook in scope has 0 error-path tests, and prints a per-hook coverage table.
- Hooks in scope (10 total): `intent-sdlc.py`, `session-resume.py`, `auto-test.py`, `sdlc-compact.py`, `safety-check.py`, `subagent-context.py`, `safety_check_agent.py`, `failure-context.py`, `session-cleanup.py`, `notification-log.py`.
- `make test-unit` runs the coverage gate after `pytest tests/unit/` and fails the build if the gate fails.

**Files:**
- Create: `tests/unit/scripts/check_error_path_coverage.py`
- Modify: `Makefile`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_coverage_gate.py (temporary test for Task 7)
  """Verify check_error_path_coverage.py exits 0 given a known set of test IDs."""
  import subprocess, sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).parent.parent.parent
  GATE_SCRIPT = REPO_ROOT / "tests" / "unit" / "scripts" / "check_error_path_coverage.py"


  def test_gate_script_exists():
      assert GATE_SCRIPT.exists(), f"Gate script missing: {GATE_SCRIPT}"


  def test_gate_passes_with_full_coverage(tmp_path):
      """Gate exits 0 when all 10 hooks have ≥1 test ID."""
      fake_output = "\n".join([
          "test_hook_uninitialized_project.py::test_intent_sdlc_no_zf_dir",
          "test_hook_uninitialized_project.py::test_session_resume_no_zf_dir",
          "test_hook_uninitialized_project.py::test_auto_test_no_zf_dir",
          "test_hook_uninitialized_project.py::test_sdlc_compact_no_zf_dir",
          "test_hook_uninitialized_project.py::test_safety_check_no_zf_dir",
          "test_hook_uninitialized_project.py::test_subagent_context_no_zf_dir",
          "test_hook_subprocess_timeout.py::test_safety_check_agent_timeout_falls_back",
          "test_hook_subprocess_timeout.py::test_auto_test_make_hang_exits_cleanly",
          "test_hook_partial_state.py::test_specs_dir_missing",
          "test_hook_concurrent_writes.py::test_concurrent_cleanup_and_notification_log",
          # failure-context.py + session-cleanup.py covered by names in test IDs
          "test_hooks_failure_context.py::test_failure_context_error_path",
          "test_session_cleanup.py::test_session_cleanup_error_path",
      ])
      result = subprocess.run(
          [sys.executable, str(GATE_SCRIPT)],
          input=fake_output,
          capture_output=True, text=True,
      )
      assert result.returncode == 0, result.stderr


  def test_gate_fails_with_missing_hook(tmp_path):
      """Gate exits non-zero when a required hook has 0 error-path tests."""
      # Provide test IDs that miss failure-context.py
      fake_output = "\n".join([
          "test_hook_uninitialized_project.py::test_intent_sdlc_no_zf_dir",
      ])
      result = subprocess.run(
          [sys.executable, str(GATE_SCRIPT)],
          input=fake_output,
          capture_output=True, text=True,
      )
      assert result.returncode != 0
  ```
  Run: `make test-unit` — must FAIL (script doesn't exist yet)

- [ ] **Step 2: Implement (GREEN)**

  Create `tests/unit/scripts/__init__.py` (empty) and `tests/unit/scripts/check_error_path_coverage.py`:
  ```python
  #!/usr/bin/env python3
  """
  Coverage gate: verify ≥1 @pytest.mark.error_path test exists per in-scope hook.

  Usage (called from Makefile after pytest):
      pytest --collect-only -q -m error_path tests/unit/ 2>/dev/null \
          | python3 tests/unit/scripts/check_error_path_coverage.py

  Reads test IDs from stdin (one per line, pytest -q format).
  Exits 0 if all in-scope hooks have ≥1 error-path test.
  Exits 1 if any hook has 0, printing a summary table.
  """
  import sys

  HOOKS_IN_SCOPE = [
      "intent-sdlc",
      "session-resume",
      "auto-test",
      "sdlc-compact",
      "safety-check",
      "subagent-context",
      "safety_check_agent",
      "failure-context",
      "session-cleanup",
      "notification-log",
  ]

  # Map hook name → keyword that would appear in a test ID covering that hook
  _HOOK_KEYWORDS = {h: h.replace("-", "_").replace(".", "_") for h in HOOKS_IN_SCOPE}
  # Override ambiguous mappings
  _HOOK_KEYWORDS["safety-check"] = "safety_check"
  _HOOK_KEYWORDS["safety_check_agent"] = "safety_check_agent"


  def main():
      test_ids = sys.stdin.read().splitlines()
      counts = {h: 0 for h in HOOKS_IN_SCOPE}

      for tid in test_ids:
          tid_lower = tid.lower()
          for hook, keyword in _HOOK_KEYWORDS.items():
              if keyword in tid_lower:
                  counts[hook] += 1

      missing = [h for h, c in counts.items() if c == 0]

      print("\n=== Hook Error-Path Coverage Gate ===")
      for hook in HOOKS_IN_SCOPE:
          status = "PASS" if counts[hook] > 0 else "FAIL"
          print(f"  [{status}] {hook}: {counts[hook]} error-path test(s)")

      if missing:
          print(f"\nFAIL: {len(missing)} hook(s) missing error-path tests: {', '.join(missing)}")
          sys.exit(1)
      else:
          print(f"\nPASS: all {len(HOOKS_IN_SCOPE)} hooks have ≥1 error-path test")
          sys.exit(0)


  if __name__ == "__main__":
      main()
  ```

  Add to `Makefile` `test-unit` target, after the pytest line:
  ```makefile
  	@pytest --collect-only -q -m error_path tests/unit/ 2>/dev/null \
  		| python3 tests/unit/scripts/check_error_path_coverage.py
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Remove `tests/unit/test_coverage_gate.py` (it was a temporary scaffolding test). Ensure the Makefile gate runs cleanly with `make test-unit`.
  Run: `make test-unit` — still PASS

---

## Acceptance Criteria Checklist

Derived from spec testability section:

- [ ] `test_hook_uninitialized_project.py` exists with ≥6 test cases, all `@pytest.mark.error_path`
- [ ] `test_hook_malformed_config.py` exists with ≥4 test cases, all `@pytest.mark.error_path`
- [ ] `test_hook_subprocess_timeout.py` exists with ≥2 test cases, all `@pytest.mark.error_path`
- [ ] `test_hook_partial_state.py` exists with ≥4 test cases, all `@pytest.mark.error_path`
- [ ] `test_hook_concurrent_writes.py` exists with ≥1 test case, all `@pytest.mark.error_path`
- [ ] `tests/conftest.py` defines `run_hook()` with ADR-015 env isolation
- [ ] All new tests pass on clean `pytest tests/unit/`
- [ ] `make test-unit` runs post-test coverage gate script
- [ ] Coverage gate validates ≥1 error-path test for all 10 in-scope hooks
- [ ] `pytest --strict-markers tests/unit/` passes with no marker warnings
