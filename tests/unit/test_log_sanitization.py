"""Tests for log field sanitization in stopfailure-log.py and notification-log.py."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
from utils_io import project_tmp_path, safe_project_name

REPO_ROOT = str(Path(__file__).parent.parent.parent)


def _run_stopfailure(event: dict, tmp_path: Path) -> str:
    (tmp_path / "zie-framework").mkdir(exist_ok=True)
    (tmp_path / "zie-framework" / "ROADMAP.md").write_text("## Now\n")
    # Clear any previous log to avoid accumulation across runs
    log = project_tmp_path("failure-log", safe_project_name(tmp_path.name))
    log.unlink(missing_ok=True)
    env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
    subprocess.run(
        [sys.executable, "hooks/stopfailure-log.py"],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    return log.read_text() if log.exists() else ""


def test_stopfailure_sanitizes_newline_in_error_type(tmp_path):
    event = {
        "hook_event_name": "StopFailure",
        "error_type": "rate_limit\nINJECTED",
        "error_details": "normal",
    }
    content = _run_stopfailure(event, tmp_path)
    assert content, "Log file should have been written"
    lines = [line for line in content.splitlines() if line.strip()]
    assert len(lines) == 1, f"Expected single log line, got {len(lines)}: {content!r}"


def test_stopfailure_sanitizes_null_byte_in_details(tmp_path):
    event = {
        "hook_event_name": "StopFailure",
        "error_type": "billing_error",
        "error_details": "bad\x00data",
    }
    content = _run_stopfailure(event, tmp_path)
    assert content, "Log file should have been written"
    assert "\x00" not in content
    assert "bad?data" in content
