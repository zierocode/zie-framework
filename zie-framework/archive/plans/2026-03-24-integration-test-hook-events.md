---
approved: false
approved_at: ~
backlog: backlog/integration-test-hook-events.md
spec: specs/2026-03-24-integration-test-hook-events-design.md
---

# Integration Tests — Mock Claude Code Hook Events End-to-End — Implementation Plan

**Goal:** Create integration tests that run every hook script as a subprocess with a realistic
Claude Code event JSON payload on stdin, asserting exit code == 0 and no Python traceback
in stderr. Tests are isolated from unit tests via the `integration` pytest marker.

**Architecture:** Three-task sequence — fixtures first, then the test module, then Makefile
wiring. The Makefile already has `test-unit` (excludes `integration` marker) and `test-int`
targets; `make test` needs to include integration alongside unit tests.

**Tech Stack:** Python 3.x (subprocess, pytest), JSON fixture files, pytest markers

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `tests/integration/__init__.py` | Makes directory a package; required for pytest discovery |
| Create | `tests/integration/fixtures/session_start_event.json` | Realistic SessionStart payload |
| Create | `tests/integration/fixtures/pretooluse_bash_event.json` | Realistic PreToolUse/Bash payload |
| Create | `tests/integration/fixtures/pretooluse_write_event.json` | Realistic PreToolUse/Write payload |
| Create | `tests/integration/fixtures/posttooluse_edit_event.json` | Realistic PostToolUse/Edit payload |
| Create | `tests/integration/fixtures/posttooluse_failure_event.json` | Realistic PostToolUseFailure/Bash payload |
| Create | `tests/integration/fixtures/stop_event.json` | Realistic Stop payload |
| Create | `tests/integration/fixtures/userpromptsubmit_event.json` | Realistic UserPromptSubmit payload |
| Create | `tests/integration/fixtures/notification_permission_event.json` | Realistic Notification/permission_prompt payload |
| Create | `tests/integration/fixtures/taskcompleted_event.json` | Realistic TaskCompleted payload |
| Create | `tests/integration/fixtures/config_change_event.json` | Realistic ConfigChange payload |
| Create | `tests/integration/fixtures/subagent_start_event.json` | Realistic SubagentStart payload |
| Create | `tests/integration/fixtures/subagent_stop_event.json` | Realistic SubagentStop payload |
| Create | `tests/integration/fixtures/precompact_event.json` | Realistic PreCompact payload |
| Create | `tests/integration/fixtures/postcompact_event.json` | Realistic PostCompact payload |
| Create | `tests/integration/fixtures/permission_request_event.json` | Realistic PermissionRequest/Bash payload |
| Create | `tests/integration/fixtures/stopfailure_event.json` | Realistic StopFailure payload |
| Create | `tests/integration/test_hook_events.py` | One test class per hook; subprocess + stdin delivery |
| Modify | `Makefile` | Wire `make test` to include integration tests |

---

## Task 1: Create `tests/integration/` directory, `__init__.py`, and all fixtures

<!-- depends_on: none -->

**Acceptance Criteria:**
- `tests/integration/__init__.py` exists (empty file)
- All 9 fixture JSON files exist under `tests/integration/fixtures/`
- Each fixture is valid JSON and contains the keys that the target hook reads
- Fixtures use realistic values (real tool names, plausible file paths, non-empty messages)

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/fixtures/session_start_event.json`
- Create: `tests/integration/fixtures/pretooluse_bash_event.json`
- Create: `tests/integration/fixtures/pretooluse_write_event.json`
- Create: `tests/integration/fixtures/posttooluse_edit_event.json`
- Create: `tests/integration/fixtures/posttooluse_failure_event.json`
- Create: `tests/integration/fixtures/stop_event.json`
- Create: `tests/integration/fixtures/userpromptsubmit_event.json`
- Create: `tests/integration/fixtures/notification_permission_event.json`
- Create: `tests/integration/fixtures/taskcompleted_event.json`
- Create: `tests/integration/fixtures/config_change_event.json`
- Create: `tests/integration/fixtures/subagent_start_event.json`
- Create: `tests/integration/fixtures/subagent_stop_event.json`
- Create: `tests/integration/fixtures/precompact_event.json`
- Create: `tests/integration/fixtures/postcompact_event.json`
- Create: `tests/integration/fixtures/permission_request_event.json`
- Create: `tests/integration/fixtures/stopfailure_event.json`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/integration/test_hook_events.py — add at top of file as a canary
  import pytest
  from pathlib import Path

  FIXTURES = Path(__file__).parent / "fixtures"

  @pytest.mark.integration
  class TestFixturesExist:
      def test_session_start_event_exists(self):
          assert (FIXTURES / "session_start_event.json").exists()

      def test_pretooluse_bash_event_exists(self):
          assert (FIXTURES / "pretooluse_bash_event.json").exists()

      def test_pretooluse_write_event_exists(self):
          assert (FIXTURES / "pretooluse_write_event.json").exists()

      def test_posttooluse_edit_event_exists(self):
          assert (FIXTURES / "posttooluse_edit_event.json").exists()

      def test_posttooluse_failure_event_exists(self):
          assert (FIXTURES / "posttooluse_failure_event.json").exists()

      def test_stop_event_exists(self):
          assert (FIXTURES / "stop_event.json").exists()

      def test_userpromptsubmit_event_exists(self):
          assert (FIXTURES / "userpromptsubmit_event.json").exists()

      def test_notification_permission_event_exists(self):
          assert (FIXTURES / "notification_permission_event.json").exists()

      def test_taskcompleted_event_exists(self):
          assert (FIXTURES / "taskcompleted_event.json").exists()

      def test_config_change_event_exists(self):
          assert (FIXTURES / "config_change_event.json").exists()

      def test_subagent_start_event_exists(self):
          assert (FIXTURES / "subagent_start_event.json").exists()

      def test_subagent_stop_event_exists(self):
          assert (FIXTURES / "subagent_stop_event.json").exists()

      def test_precompact_event_exists(self):
          assert (FIXTURES / "precompact_event.json").exists()

      def test_postcompact_event_exists(self):
          assert (FIXTURES / "postcompact_event.json").exists()

      def test_permission_request_event_exists(self):
          assert (FIXTURES / "permission_request_event.json").exists()

      def test_stopfailure_event_exists(self):
          assert (FIXTURES / "stopfailure_event.json").exists()
  ```

  Run: `make test-int` — must FAIL (fixtures do not exist yet)

- [ ] **Step 2: Implement (GREEN)**

  Create `tests/integration/__init__.py` (empty).

  Create `tests/integration/fixtures/session_start_event.json`:
  ```json
  {
    "event": "SessionStart",
    "session_id": "test-session-001"
  }
  ```

  Create `tests/integration/fixtures/pretooluse_bash_event.json`:
  ```json
  {
    "event": "PreToolUse",
    "tool_name": "Bash",
    "tool_input": {
      "command": "make test-unit"
    }
  }
  ```

  Create `tests/integration/fixtures/pretooluse_write_event.json`:
  ```json
  {
    "event": "PreToolUse",
    "tool_name": "Write",
    "tool_input": {
      "file_path": "hooks/test_output.py",
      "content": "# placeholder"
    }
  }
  ```

  Create `tests/integration/fixtures/posttooluse_edit_event.json`:
  ```json
  {
    "event": "PostToolUse",
    "tool_name": "Edit",
    "tool_input": {
      "file_path": "/tmp/zie-integration-test-dummy.py"
    },
    "tool_response": {
      "result": "ok"
    }
  }
  ```

  Create `tests/integration/fixtures/posttooluse_failure_event.json`:
  ```json
  {
    "event": "PostToolUseFailure",
    "tool_name": "Bash",
    "tool_input": {
      "command": "make test-unit"
    },
    "is_interrupt": false,
    "error": "Command exited with code 1"
  }
  ```

  Create `tests/integration/fixtures/stop_event.json`:
  ```json
  {
    "event": "Stop",
    "stop_reason": "end_turn",
    "stop_hook_active": false
  }
  ```

  Create `tests/integration/fixtures/userpromptsubmit_event.json`:
  ```json
  {
    "event": "UserPromptSubmit",
    "prompt": "implement the next task"
  }
  ```

  Create `tests/integration/fixtures/notification_permission_event.json`:
  ```json
  {
    "event": "Notification",
    "notification_type": "permission_prompt",
    "message": "Allow Bash: make test-unit?"
  }
  ```

  Create `tests/integration/fixtures/taskcompleted_event.json`:
  ```json
  {
    "event": "TaskCompleted",
    "tool_name": "TaskCompleted",
    "tool_input": {
      "title": "implement integration tests"
    }
  }
  ```

  Create `tests/integration/fixtures/config_change_event.json`:
  ```json
  {
    "event": "ConfigChange",
    "config_key": "model",
    "new_value": "claude-opus-4-6"
  }
  ```

  Create `tests/integration/fixtures/subagent_start_event.json`:
  ```json
  {
    "event": "SubagentStart",
    "subagent_id": "test-subagent-001",
    "task": "implement feature X"
  }
  ```

  Create `tests/integration/fixtures/subagent_stop_event.json`:
  ```json
  {
    "event": "SubagentStop",
    "subagent_id": "test-subagent-001",
    "stop_reason": "end_turn"
  }
  ```

  Create `tests/integration/fixtures/precompact_event.json`:
  ```json
  {
    "event": "PreCompact",
    "trigger": "context_limit"
  }
  ```

  Create `tests/integration/fixtures/postcompact_event.json`:
  ```json
  {
    "event": "PostCompact",
    "trigger": "context_limit",
    "summary": "Session compacted successfully"
  }
  ```

  Create `tests/integration/fixtures/permission_request_event.json`:
  ```json
  {
    "event": "PermissionRequest",
    "tool_name": "Bash",
    "tool_input": {
      "command": "make test"
    }
  }
  ```

  Create `tests/integration/fixtures/stopfailure_event.json`:
  ```json
  {
    "event": "StopFailure",
    "error": "Response generation failed unexpectedly"
  }
  ```

  Run: `make test-int` — must PASS

- [ ] **Step 3: Refactor**

  Verify each JSON file loads cleanly: `python3 -c "import json, pathlib; [json.loads(p.read_text()) for p in pathlib.Path('tests/integration/fixtures').glob('*.json')]"`.
  Run: `make test-int` — still PASS

---

## Task 2: Create `tests/integration/test_hook_events.py` with one test per hook

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- One test class per hook script mapped in `hooks.json`
- Each test delivers the matching fixture JSON via stdin as a subprocess
- All tests assert: `returncode == 0`, `"Traceback" not in stderr`
- All test classes are marked `@pytest.mark.integration`
- Tests set `CLAUDE_CWD` env var pointing to the repo root so hooks find `zie-framework/`
- `make test-int` runs all tests; `make test-unit` does not collect any of them

**Files:**
- Create: `tests/integration/test_hook_events.py`

- [ ] **Step 1: Write failing tests (RED)**

  The `TestFixturesExist` canary from Task 1 is the RED guard for this task — the hook
  tests themselves will be the new additions. Write the full test module now; it will fail
  until the hook runner helper is wired.

  ```python
  # tests/integration/test_hook_events.py
  """Integration tests — run each hook as a subprocess with a realistic event payload.

  Each test:
    - Reads a fixture JSON from tests/integration/fixtures/
    - Runs the hook script via subprocess with the fixture on stdin
    - Asserts exit code == 0
    - Asserts no unhandled Python traceback in stderr

  Environment:
    CLAUDE_CWD is set to the repo root so hooks that check for zie-framework/ find it.
    No live Claude Code process is required.
  """
  import json
  import os
  import subprocess
  import sys
  import pytest
  from pathlib import Path

  REPO_ROOT = Path(__file__).parents[2]
  HOOKS_DIR = REPO_ROOT / "hooks"
  FIXTURES   = Path(__file__).parent / "fixtures"


  def run_hook(hook_name: str, fixture_name: str, extra_env: dict = None) -> subprocess.CompletedProcess:
      """Run a hook script with a fixture JSON on stdin.

      Args:
          hook_name:    Filename under hooks/, e.g. "session-resume.py"
          fixture_name: Filename under tests/integration/fixtures/, e.g. "session_start_event.json"
          extra_env:    Extra environment variables to set (merged on top of os.environ).

      Returns:
          CompletedProcess with stdout, stderr, returncode.
      """
      hook_path = HOOKS_DIR / hook_name
      fixture_path = FIXTURES / fixture_name
      stdin_data = fixture_path.read_text()

      env = os.environ.copy()
      env["CLAUDE_CWD"] = str(REPO_ROOT)
      if extra_env:
          env.update(extra_env)

      return subprocess.run(
          [sys.executable, str(hook_path)],
          input=stdin_data,
          capture_output=True,
          text=True,
          env=env,
      )


  def assert_clean_exit(result: subprocess.CompletedProcess) -> None:
      """Assert exit code == 0 and no unhandled Python traceback in stderr."""
      assert result.returncode == 0, (
          f"Hook exited {result.returncode}\n"
          f"stdout: {result.stdout!r}\n"
          f"stderr: {result.stderr!r}"
      )
      assert "Traceback (most recent call last)" not in result.stderr, (
          f"Unhandled traceback in stderr:\n{result.stderr}"
      )


  # ---------------------------------------------------------------------------
  # SessionStart
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestSessionResumeHook:
      def test_exits_zero_with_session_start_event(self):
          result = run_hook("session-resume.py", "session_start_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("session-resume.py", "session_start_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # UserPromptSubmit — intent-detect.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestIntentDetectHook:
      def test_exits_zero_with_userpromptsubmit_event(self):
          result = run_hook("intent-detect.py", "userpromptsubmit_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("intent-detect.py", "userpromptsubmit_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # UserPromptSubmit — sdlc-context.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestSdlcContextHook:
      def test_exits_zero_with_userpromptsubmit_event(self):
          result = run_hook("sdlc-context.py", "userpromptsubmit_event.json")
          assert_clean_exit(result)

      def test_stdout_is_valid_json_when_nonempty(self):
          result = run_hook("sdlc-context.py", "userpromptsubmit_event.json")
          assert_clean_exit(result)
          if result.stdout.strip():
              parsed = json.loads(result.stdout.strip())
              assert isinstance(parsed, dict)


  # ---------------------------------------------------------------------------
  # PreToolUse — safety-check.py (Bash event)
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestSafetyCheckHook:
      def test_exits_zero_for_safe_bash_command(self):
          result = run_hook("safety-check.py", "pretooluse_bash_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("safety-check.py", "pretooluse_bash_event.json")
          assert "Traceback" not in result.stderr

      def test_non_bash_tool_exits_zero(self):
          result = run_hook("safety-check.py", "pretooluse_write_event.json")
          assert_clean_exit(result)


  # ---------------------------------------------------------------------------
  # PreToolUse — input-sanitizer.py (Write event with relative path)
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestInputSanitizerHook:
      def test_exits_zero_for_write_event(self):
          result = run_hook("input-sanitizer.py", "pretooluse_write_event.json")
          assert_clean_exit(result)

      def test_exits_zero_for_bash_event(self):
          result = run_hook("input-sanitizer.py", "pretooluse_bash_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("input-sanitizer.py", "pretooluse_write_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # PostToolUse — auto-test.py (Edit event)
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestAutoTestHook:
      def test_exits_zero_for_edit_event(self):
          result = run_hook("auto-test.py", "posttooluse_edit_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("auto-test.py", "posttooluse_edit_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # PostToolUse — wip-checkpoint.py (Edit event, no memory keys set)
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestWipCheckpointHook:
      def test_exits_zero_without_memory_keys(self):
          # ZIE_MEMORY_API_KEY absent → hook should fast-exit cleanly
          env = {"ZIE_MEMORY_API_KEY": "", "ZIE_MEMORY_API_URL": ""}
          result = run_hook("wip-checkpoint.py", "posttooluse_edit_event.json", extra_env=env)
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          env = {"ZIE_MEMORY_API_KEY": "", "ZIE_MEMORY_API_URL": ""}
          result = run_hook("wip-checkpoint.py", "posttooluse_edit_event.json", extra_env=env)
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # PostToolUseFailure — failure-context.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestFailureContextHook:
      def test_exits_zero_for_bash_failure_event(self):
          result = run_hook("failure-context.py", "posttooluse_failure_event.json")
          assert_clean_exit(result)

      def test_stdout_is_valid_json(self):
          result = run_hook("failure-context.py", "posttooluse_failure_event.json")
          assert_clean_exit(result)
          if result.stdout.strip():
              parsed = json.loads(result.stdout.strip())
              assert "additionalContext" in parsed

      def test_produces_no_traceback(self):
          result = run_hook("failure-context.py", "posttooluse_failure_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # Stop — stop-guard.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestStopGuardHook:
      def test_exits_zero_with_stop_event(self):
          result = run_hook("stop-guard.py", "stop_event.json")
          assert_clean_exit(result)

      def test_exits_zero_when_stop_hook_active(self):
          # Infinite-loop guard: stop_hook_active == true → must exit immediately
          payload = json.dumps({"event": "Stop", "stop_reason": "end_turn", "stop_hook_active": True})
          hook_path = HOOKS_DIR / "stop-guard.py"
          env = os.environ.copy()
          env["CLAUDE_CWD"] = str(REPO_ROOT)
          result = subprocess.run(
              [sys.executable, str(hook_path)],
              input=payload,
              capture_output=True,
              text=True,
              env=env,
          )
          assert result.returncode == 0
          assert "Traceback" not in result.stderr

      def test_produces_no_traceback(self):
          result = run_hook("stop-guard.py", "stop_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # Stop — session-learn.py (no memory keys set)
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestSessionLearnHook:
      def test_exits_zero_without_memory_keys(self):
          env = {"ZIE_MEMORY_API_KEY": "", "ZIE_MEMORY_API_URL": ""}
          result = run_hook("session-learn.py", "stop_event.json", extra_env=env)
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          env = {"ZIE_MEMORY_API_KEY": "", "ZIE_MEMORY_API_URL": ""}
          result = run_hook("session-learn.py", "stop_event.json", extra_env=env)
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # Stop — session-cleanup.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestSessionCleanupHookIntegration:
      def test_exits_zero_with_stop_event(self):
          result = run_hook("session-cleanup.py", "stop_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("session-cleanup.py", "stop_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # Notification — notification-log.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestNotificationLogHook:
      def test_exits_zero_with_permission_prompt_event(self):
          result = run_hook("notification-log.py", "notification_permission_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("notification-log.py", "notification_permission_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # TaskCompleted — task-completed-gate.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestTaskCompletedGateHook:
      def test_exits_zero_with_implement_task(self):
          result = run_hook("task-completed-gate.py", "taskcompleted_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("task-completed-gate.py", "taskcompleted_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # PreToolUse/Bash — safety_check_agent.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestSafetyCheckAgentHook:
      def test_exits_zero_for_bash_event(self):
          result = run_hook("safety_check_agent.py", "pretooluse_bash_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("safety_check_agent.py", "pretooluse_bash_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # ConfigChange — config-drift.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestConfigDriftHook:
      def test_exits_zero_for_config_change_event(self):
          result = run_hook("config-drift.py", "config_change_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("config-drift.py", "config_change_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # SubagentStart — subagent-context.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestSubagentContextHook:
      def test_exits_zero_for_subagent_start_event(self):
          result = run_hook("subagent-context.py", "subagent_start_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("subagent-context.py", "subagent_start_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # SubagentStop — subagent-stop.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestSubagentStopHook:
      def test_exits_zero_for_subagent_stop_event(self):
          result = run_hook("subagent-stop.py", "subagent_stop_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("subagent-stop.py", "subagent_stop_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # PreCompact + PostCompact — sdlc-compact.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestSdlcCompactHook:
      def test_exits_zero_for_precompact_event(self):
          result = run_hook("sdlc-compact.py", "precompact_event.json")
          assert_clean_exit(result)

      def test_exits_zero_for_postcompact_event(self):
          result = run_hook("sdlc-compact.py", "postcompact_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("sdlc-compact.py", "precompact_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # PermissionRequest/Bash — sdlc-permissions.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestSdlcPermissionsHook:
      def test_exits_zero_for_permission_request_event(self):
          result = run_hook("sdlc-permissions.py", "permission_request_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("sdlc-permissions.py", "permission_request_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # StopFailure — stopfailure-log.py
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestStopfailureLogHook:
      def test_exits_zero_for_stopfailure_event(self):
          result = run_hook("stopfailure-log.py", "stopfailure_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("stopfailure-log.py", "stopfailure_event.json")
          assert "Traceback" not in result.stderr


  # ---------------------------------------------------------------------------
  # knowledge-hash.py (in hooks/, tested with posttooluse event)
  # ---------------------------------------------------------------------------

  @pytest.mark.integration
  class TestKnowledgeHashHook:
      def test_exits_zero_for_posttooluse_event(self):
          result = run_hook("knowledge-hash.py", "posttooluse_edit_event.json")
          assert_clean_exit(result)

      def test_produces_no_traceback(self):
          result = run_hook("knowledge-hash.py", "posttooluse_edit_event.json")
          assert "Traceback" not in result.stderr
  ```

  Run: `make test-int` — must FAIL (test file does not yet exist at this point in the
  flow; once written, the fixture canary tests from Task 1 already pass, so the hook
  tests themselves become the new RED targets until Task 1 fixtures are confirmed present)

- [ ] **Step 2: Implement (GREEN)**

  Write `tests/integration/test_hook_events.py` with the full content above.
  Run: `make test-int` — must PASS (all hooks exit 0, no tracebacks)

- [ ] **Step 3: Refactor**

  - Confirm `run_hook` helper covers all hooks without duplication.
  - Confirm every hook in `hooks.json` has at least one corresponding test class.
  - Confirm `@pytest.mark.integration` is present on all classes.
  - Run: `make test-unit` — must collect ZERO integration tests.
  - Run: `make test-int` — still PASS.

---

## Task 3: Update `Makefile` — wire `make test` to include integration tests

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `make test` runs both unit and integration tests (not just unit + lint)
- `make test-unit` still excludes integration tests (unchanged)
- `make test-int` still runs only integration tests (unchanged)
- `pytest.ini` or `pyproject.toml` registers the `integration` marker to suppress
  PytestUnknownMarkWarning if not already registered

**Files:**
- Modify: `Makefile`
- Modify: `pytest.ini` or `pyproject.toml` (whichever configures pytest markers)

- [ ] **Step 1: Write failing tests (RED)**

  Manual verification step — no automated test exists for Makefile targets, but
  confirm the current state: `make test` does NOT run integration tests.

  ```bash
  make test 2>&1 | grep -c "integration"
  # Expected: 0  (integration tests not yet included in make test)
  ```

- [ ] **Step 2: Implement (GREEN)**

  Current `Makefile` line 16:
  ```makefile
  test: test-unit lint-md ## Full test suite (unit + integration + md lint)
  ```

  Replace with:
  ```makefile
  test: test-unit test-int lint-md ## Full test suite (unit + integration + md lint)
  ```

  Check whether `pytest.ini` exists. If not, check `pyproject.toml`. Register the marker
  in whichever file is active:

  If using `pytest.ini`:
  ```ini
  [pytest]
  markers =
      integration: marks tests as integration tests (run with make test-int)
  ```

  If using `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  markers = [
      "integration: marks tests as integration tests (run with make test-int)",
  ]
  ```

  Run: `make test` — must PASS (unit + integration + lint all green)

- [ ] **Step 3: Refactor**

  Run `make test-unit` — confirm integration tests are excluded (0 collected from
  `tests/integration/`).
  Run `make test-int` — confirm only integration tests run.
  Run `make test` — confirm all three suites pass end to end.

---

*Commit: `git add tests/integration/ Makefile && git add pytest.ini pyproject.toml 2>/dev/null; git commit -m "feat: integration-test-hook-events"`*
