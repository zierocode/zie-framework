"""Tests for JSON protocol fix in sdlc-compact.py and auto-test.py."""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = str(Path(__file__).parent.parent.parent)


def _run_hook(hook: str, event: dict) -> dict | None:
    result = subprocess.run(
        [sys.executable, f"hooks/{hook}"],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if result.stdout.strip():
        return json.loads(result.stdout.strip())
    return None


def test_sdlc_compact_no_hookspecificoutput():
    """sdlc-compact must emit flat additionalContext, not hookSpecificOutput wrapper."""
    event = {"hook_event_name": "PreCompact", "summary": "test summary"}
    result = _run_hook("sdlc-compact.py", event)
    if result is not None:
        assert "hookSpecificOutput" not in result
        assert "additionalContext" in result


def test_auto_test_no_hookspecificoutput(tmp_path):
    """auto-test must emit flat additionalContext, not hookSpecificOutput wrapper."""
    import os

    (tmp_path / "foo.py").write_text("x = 1")
    (tmp_path / "test_foo.py").write_text("def test_x(): pass")
    event = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(tmp_path / "foo.py")},
        "tool_response": {},
    }
    env = {**os.environ, "CLAUDE_TOOL_CWD": str(tmp_path)}
    result = subprocess.run(
        [sys.executable, "hooks/auto-test.py"],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    if result.stdout.strip():
        parsed = json.loads(result.stdout.strip())
        assert "hookSpecificOutput" not in parsed
        assert "additionalContext" in parsed
