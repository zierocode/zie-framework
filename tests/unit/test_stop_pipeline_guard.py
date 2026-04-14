"""Unit tests for hooks/stop-handler.py — sprint intent guard (merged v1.29.0)."""
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "stop-handler.py"


def _flag(project: str, name: str) -> Path:
    safe = re.sub(r'[^a-zA-Z0-9]', '-', project)
    return Path(tempfile.gettempdir()) / f"zie-{safe}-{name}"


def _clean_nudge_cache(session_id: str) -> None:
    """Clean nudge-check cache for a session."""
    safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)
    cache_dir = Path(tempfile.gettempdir()) / f"zie-{safe_id}"
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)


def _run(tmp_path: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    env["CLAUDE_SESSION_ID"] = "test-session"
    event = json.dumps({"session_id": "test-session", "stop_reason": "end_turn"})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event, capture_output=True, text=True, env=env,
    )


def _make_zf(tmp_path: Path) -> Path:
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    (zf / "specs").mkdir(exist_ok=True)
    (zf / "plans").mkdir(exist_ok=True)
    return zf


def _approved_spec(zf: Path) -> Path:
    today = date.today().isoformat()
    p = zf / "specs" / f"{today}-test-design.md"
    p.write_text("---\napproved: true\napproved_at: 2026-04-11\n---\n# Test\n")
    return p


def _approved_plan(zf: Path) -> Path:
    today = date.today().isoformat()
    p = zf / "plans" / f"{today}-test.md"
    p.write_text("---\napproved: true\napproved_at: 2026-04-11\n---\n# Plan\n")
    return p


class TestStopPipelineGuard:
    def test_exits_zero_when_no_sprint_flag(self, tmp_path):
        _make_zf(tmp_path)
        r = _run(tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == "", "must produce no output when sprint flag absent"

    def test_warns_when_sprint_flag_no_artifacts(self, tmp_path):
        zf = _make_zf(tmp_path)
        flag = _flag(tmp_path.name, "intent-sprint-flag")
        flag.write_text("active")
        _clean_nudge_cache("test-session")
        r = _run(tmp_path)
        assert r.returncode == 0
        assert "sprint intent" in r.stdout.lower() or "sprint intent" in r.stderr.lower(), (
            "must warn about sprint intent without approved artifacts"
        )
        flag.unlink(missing_ok=True)

    def test_silent_when_sprint_flag_and_approved_spec(self, tmp_path):
        zf = _make_zf(tmp_path)
        _approved_spec(zf)
        flag = _flag(tmp_path.name, "intent-sprint-flag")
        flag.write_text("active")
        _clean_nudge_cache("test-session")
        r = _run(tmp_path)
        assert r.returncode == 0
        # With approved artifacts, no warning emitted
        output = r.stdout + r.stderr
        assert "sprint intent detected but no approved" not in output.lower()
        flag.unlink(missing_ok=True)

    def test_silent_when_sprint_flag_and_approved_plan(self, tmp_path):
        zf = _make_zf(tmp_path)
        _approved_plan(zf)
        flag = _flag(tmp_path.name, "intent-sprint-flag")
        flag.write_text("active")
        _clean_nudge_cache("test-session")
        r = _run(tmp_path)
        assert r.returncode == 0
        output = r.stdout + r.stderr
        assert "sprint intent detected but no approved" not in output.lower()
        flag.unlink(missing_ok=True)

    def test_deletes_sprint_flag_after_check(self, tmp_path):
        _make_zf(tmp_path)
        flag = _flag(tmp_path.name, "intent-sprint-flag")
        flag.write_text("active")
        _clean_nudge_cache("test-session")
        _run(tmp_path)
        assert not flag.exists(), "sprint flag must be deleted after guard runs"

    def test_exits_zero_when_no_zf_dir(self, tmp_path):
        # No zie-framework/ dir — guard not applicable
        r = _run(tmp_path)
        assert r.returncode == 0

    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self, tmp_path):
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json", capture_output=True, text=True, env=env,
        )
        assert r.returncode == 0
