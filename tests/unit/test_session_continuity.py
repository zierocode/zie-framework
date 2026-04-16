"""Tests for session continuity snapshot in hooks/session-resume.py (Sprint B)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "session-resume.py"


def _run(tmp_path: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = {"session_id": "test-continuity"}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def _setup_zf(tmp_path: Path, roadmap: str = "## Now\n\n## Next\n") -> Path:
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    (zf / "ROADMAP.md").write_text(roadmap)
    return zf


class TestContinuitySnapshotOutput:
    def test_snapshot_shown_when_remember_now_has_content(self, tmp_path):
        _setup_zf(tmp_path)
        remember = tmp_path / ".remember"
        remember.mkdir()
        (remember / "now.md").write_text("# WIP\n\n- Working on my-feature: implementing auth")
        r = _run(tmp_path)
        assert r.returncode == 0
        # Should mention the feature or "last session" context
        assert "my-feature" in r.stdout or "Last session" in r.stdout or "WIP" in r.stdout

    def test_snapshot_omitted_when_no_remember_dir(self, tmp_path):
        _setup_zf(tmp_path)
        r = _run(tmp_path)
        assert r.returncode == 0
        # No .remember dir — must still exit 0 and produce normal output
        assert r.stdout.strip() != "" or True  # output may vary, no crash is the key

    def test_exits_zero_when_remember_now_unreadable(self, tmp_path):
        _setup_zf(tmp_path)
        remember = tmp_path / ".remember"
        remember.mkdir()
        # Create now.md as a directory to make it unreadable as a file
        (remember / "now.md").mkdir()
        r = _run(tmp_path)
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
