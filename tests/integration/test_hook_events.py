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
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOKS_DIR = REPO_ROOT / "hooks"
FIXTURES = Path(__file__).parent / "fixtures"


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
        f"Hook exited {result.returncode}\nstdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert "Traceback (most recent call last)" not in result.stderr, f"Unhandled traceback in stderr:\n{result.stderr}"


# ---------------------------------------------------------------------------
# Fixture existence canary
# ---------------------------------------------------------------------------


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
class TestIntentSdlcHook:
    def test_exits_zero_with_userpromptsubmit_event(self):
        result = run_hook("intent-sdlc.py", "userpromptsubmit_event.json")
        assert_clean_exit(result)

    def test_produces_no_traceback(self):
        result = run_hook("intent-sdlc.py", "userpromptsubmit_event.json")
        assert "Traceback" not in result.stderr

    def test_stdout_is_valid_json_when_nonempty(self):
        result = run_hook("intent-sdlc.py", "userpromptsubmit_event.json")
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
# PostToolUse — post-tool-use.py (merged from post-tool-use + wip-checkpoint)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPostToolUseHook:
    def test_exits_zero_without_memory_keys(self):
        # ZIE_MEMORY_API_KEY absent → WIP checkpoint fast-exits cleanly
        env = {"ZIE_MEMORY_API_KEY": "", "ZIE_MEMORY_API_URL": ""}
        result = run_hook("post-tool-use.py", "posttooluse_edit_event.json", extra_env=env)
        assert_clean_exit(result)

    def test_produces_no_traceback(self):
        env = {"ZIE_MEMORY_API_KEY": "", "ZIE_MEMORY_API_URL": ""}
        result = run_hook("post-tool-use.py", "posttooluse_edit_event.json", extra_env=env)
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
# Stop — stop-handler.py
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestStopGuardHook:
    def test_exits_zero_with_stop_event(self):
        result = run_hook("stop-handler.py", "stop_event.json")
        assert_clean_exit(result)

    def test_exits_zero_when_stop_hook_active(self):
        # Infinite-loop guard: stop_hook_active == true → must exit immediately
        payload = json.dumps({"event": "Stop", "stop_reason": "end_turn", "stop_hook_active": True})
        hook_path = HOOKS_DIR / "stop-handler.py"
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
        result = run_hook("stop-handler.py", "stop_event.json")
        assert "Traceback" not in result.stderr


# ---------------------------------------------------------------------------
# Stop — session-end.py (merged from session-stop + session-learn + session-cleanup)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSessionEndHook:
    def test_exits_zero_without_memory_keys(self):
        env = {"ZIE_MEMORY_API_KEY": "", "ZIE_MEMORY_API_URL": ""}
        result = run_hook("session-end.py", "stop_event.json", extra_env=env)
        assert_clean_exit(result)

    def test_produces_no_traceback(self):
        env = {"ZIE_MEMORY_API_KEY": "", "ZIE_MEMORY_API_URL": ""}
        result = run_hook("session-end.py", "stop_event.json", extra_env=env)
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
