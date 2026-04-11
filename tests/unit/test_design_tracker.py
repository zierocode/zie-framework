"""Unit tests for hooks/design-tracker.py (Area 1 — Conversation Capture)."""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "design-tracker.py"


def _run(message: str, tmp_path: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"prompt": message, "session_id": "test-session"})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event,
        capture_output=True,
        text=True,
        env=env,
    )


def _flag_path(tmp_path: Path) -> Path:
    project = tmp_path.name
    safe = re.sub(r'[^a-zA-Z0-9]', '-', project)
    return Path(tempfile.gettempdir()) / f"zie-{safe}-design-mode"


class TestDesignTrackerWritesFlag:
    def test_writes_flag_on_design_signal(self, tmp_path):
        flag = _flag_path(tmp_path)
        flag.unlink(missing_ok=True)
        r = _run("let's design a new feature for the API", tmp_path)
        assert r.returncode == 0
        assert flag.exists(), "design-mode flag must be written when design signal detected"
        flag.unlink(missing_ok=True)

    def test_no_flag_when_no_signals(self, tmp_path):
        flag = _flag_path(tmp_path)
        flag.unlink(missing_ok=True)
        r = _run("print hello world", tmp_path)
        assert r.returncode == 0
        assert not flag.exists(), "design-mode flag must NOT be written with no signals"

    def test_exits_zero_on_empty_message(self, tmp_path):
        r = _run("", tmp_path)
        assert r.returncode == 0

    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self, tmp_path):
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
