"""Unit tests for hooks/design-tracker.py (Area 1 — Conversation Capture)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "hooks"))
from utils_cache import CacheManager

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "design-tracker.py"

SESSION_ID = "test-session"


def _run(message: str, tmp_path: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"prompt": message, "session_id": SESSION_ID})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event,
        capture_output=True,
        text=True,
        env=env,
    )


class TestDesignTrackerWritesFlag:
    def test_writes_flag_on_design_signal(self, tmp_path):
        r = _run("let's design a new feature for the API", tmp_path)
        assert r.returncode == 0
        # Verify flag via CacheManager (unified session cache)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        assert cache.has_flag("design-mode", SESSION_ID), "design-mode flag must be written when design signal detected"

    def test_no_flag_when_no_signals(self, tmp_path):
        r = _run("print hello world", tmp_path)
        assert r.returncode == 0
        cache = CacheManager(tmp_path / ".zie" / "cache")
        assert not cache.has_flag("design-mode", SESSION_ID), "design-mode flag must NOT be written with no signals"

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
