"""Error-path tests for all hooks — subprocess-based.

Validates ADR-003: hooks exit 0 even on error, with graceful degradation.
Each test runs the hook as a subprocess with malformed/edge-case input
and asserts exit code is 0.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.error_path

HOOKS_DIR = Path(__file__).parents[2] / "hooks"


def _run_hook(script_name: str, stdin_data: str, env: dict = None) -> subprocess.CompletedProcess:
    """Run a hook script as subprocess with stdin, return CompletedProcess."""
    hook_path = HOOKS_DIR / script_name
    env_vars = {**os.environ, "CLAUDE_SESSION_ID": "test-session"}
    if env:
        env_vars.update(env)
    return subprocess.run(
        [sys.executable, str(hook_path)],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=10,
        env=env_vars,
    )


# --- Hooks with hyphenated filenames (can't import directly) ---


class TestSdlcCompactErrorPaths:
    """Error-path coverage for sdlc-compact.py."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0."""
        result = _run_hook("sdlc-compact.py", "not-json")
        assert result.returncode == 0

    def test_empty_stdin_exits_0(self):
        """Empty stdin should exit 0."""
        result = _run_hook("sdlc-compact.py", "")
        assert result.returncode == 0


class TestSafetyCheckErrorPaths:
    """Error-path coverage for safety-check.py."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0 (allow on error)."""
        result = _run_hook("safety-check.py", "not-json")
        assert result.returncode == 0

    def test_path_outside_project_exits_0(self):
        """Path outside project dir should exit 0 (allow)."""
        event = json.dumps(
            {
                "session_id": "test",
                "tool_name": "Write",
                "tool_input": {"file_path": "/etc/passwd"},
            }
        )
        result = _run_hook("safety-check.py", event)
        assert result.returncode == 0


class TestSubagentContextErrorPaths:
    """Error-path coverage for subagent-context.py."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0."""
        result = _run_hook("subagent-context.py", "not-json")
        assert result.returncode == 0

    def test_missing_cwd_exits_0(self):
        """Missing cwd should exit 0."""
        event = json.dumps(
            {
                "session_id": "test",
                "tool_name": "Agent",
                "tool_input": {"prompt": "test"},
            }
        )
        result = _run_hook("subagent-context.py", event)
        assert result.returncode == 0


class TestFailureContextErrorPaths:
    """Error-path coverage for failure-context.py."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0."""
        result = _run_hook("failure-context.py", "not-json")
        assert result.returncode == 0

    def test_interrupt_event_exits_0(self):
        """Interrupt event with missing fields should exit 0."""
        event = json.dumps(
            {
                "session_id": "test",
                "is_interrupt": True,
                "tool_name": "Bash",
                "tool_input": {"command": "test"},
            }
        )
        result = _run_hook("failure-context.py", event)
        assert result.returncode == 0


class TestSessionEndErrorPaths:
    """Error-path coverage for session-end.py (merged from session-stop + session-learn + session-cleanup)."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0."""
        result = _run_hook("session-end.py", "not-json")
        assert result.returncode == 0

    def test_empty_event_exits_0(self):
        """Empty event dict should exit 0."""
        event = json.dumps(
            {
                "session_id": "test-sess",
                "message": {"role": "user", "content": "bye"},
            }
        )
        result = _run_hook("session-end.py", event)
        assert result.returncode == 0


class TestNotificationLogErrorPaths:
    """Error-path coverage for notification-log.py."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0."""
        result = _run_hook("notification-log.py", "not-json")
        assert result.returncode == 0


class TestSafetyCheckReviewerGateErrorPaths:
    """Error-path coverage for reviewer-gate (now inside safety-check.py)."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0 (allow on error)."""
        result = _run_hook("safety-check.py", "not-json")
        assert result.returncode == 0

    def test_tool_use_event_exits_0(self):
        """ToolUse event for non-file tool should exit 0."""
        event = json.dumps(
            {
                "session_id": "test",
                "tool_name": "Bash",
                "tool_input": {"command": "echo hello"},
            }
        )
        result = _run_hook("safety-check.py", event)
        assert result.returncode == 0


class TestDesignTrackerErrorPaths:
    """Error-path coverage for design-tracker (now inside intent-sdlc.py)."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0."""
        result = _run_hook("intent-sdlc.py", "not-json")
        assert result.returncode == 0


class TestSessionLearnErrorPaths:
    """Error-path coverage for session-learn (now inside session-end.py)."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0."""
        result = _run_hook("session-end.py", "not-json")
        assert result.returncode == 0

    def test_assistant_end_turn_exits_0(self):
        """Assistant end_turn event should exit 0."""
        event = json.dumps(
            {
                "session_id": "test-sess",
                "message": {"role": "assistant", "content": "test"},
                "stop_reason": "end_turn",
            }
        )
        result = _run_hook("session-end.py", event)
        assert result.returncode == 0


class TestSessionResumeErrorPaths:
    """Error-path coverage for session-resume.py."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0."""
        result = _run_hook("session-resume.py", "not-json")
        assert result.returncode == 0

    def test_missing_cwd_exits_0(self):
        """Missing cwd should exit 0."""
        event = json.dumps(
            {
                "session_id": "test",
                "message": {"role": "user", "content": "hi"},
            }
        )
        result = _run_hook("session-resume.py", event)
        assert result.returncode == 0


class TestIntentSdlcErrorPaths:
    """Error-path coverage for intent-sdlc.py."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0."""
        result = _run_hook("intent-sdlc.py", "not-json")
        assert result.returncode == 0

    def test_user_message_exits_0(self):
        """User message event should exit 0."""
        event = json.dumps(
            {
                "session_id": "test",
                "message": {"role": "user", "content": "hello"},
            }
        )
        result = _run_hook("intent-sdlc.py", event)
        assert result.returncode == 0


class TestStopHandlerErrorPaths:
    """Error-path coverage for stop-handler.py."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0."""
        result = _run_hook("stop-handler.py", "not-json")
        assert result.returncode == 0

    def test_empty_stdin_exits_0(self):
        """Empty stdin should exit 0."""
        result = _run_hook("stop-handler.py", "")
        assert result.returncode == 0


class TestAutoTestErrorPaths:
    """Error-path coverage for auto-test.py."""

    def test_malformed_json_exits_0(self):
        """Malformed event JSON should exit 0."""
        result = _run_hook("auto-test.py", "not-json")
        assert result.returncode == 0

    def test_tool_use_event_exits_0(self):
        """ToolUse event for test tool should exit 0."""
        event = json.dumps(
            {
                "session_id": "test",
                "tool_name": "Bash",
                "tool_input": {"command": "pytest test_x.py"},
            }
        )
        result = _run_hook("auto-test.py", event)
        assert result.returncode == 0
