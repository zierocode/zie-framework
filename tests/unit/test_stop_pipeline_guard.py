"""Unit tests for hooks/stop-handler.py — sprint intent guard (merged v1.29.0)."""

import json
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "stop-handler.py"
sys.path.insert(0, str(REPO_ROOT / "hooks"))
from utils_cache import CacheManager


def _unique_session() -> str:
    """Generate unique session ID to avoid stale /tmp nudge-check caches."""
    return f"test-{uuid.uuid4().hex[:8]}"


def _clean_git_caches(session_id: str) -> None:
    """Remove stale /tmp git-status and nudge-check caches for this session."""
    safe_id = __import__("re").sub(r"[^a-zA-Z0-9_-]", "-", session_id)
    cache_dir = Path(tempfile.gettempdir()) / f"zie-{safe_id}"
    if cache_dir.exists():
        for f in cache_dir.glob("git-*.cache"):
            f.unlink(missing_ok=True)


def _run(tmp_path: Path, session_id: str = "test-session") -> subprocess.CompletedProcess:
    _clean_git_caches(session_id)
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    env["CLAUDE_SESSION_ID"] = session_id
    event = json.dumps({"session_id": session_id, "stop_reason": "end_turn"})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event,
        capture_output=True,
        text=True,
        env=env,
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
        # May or may not produce output (nudge checks), but must exit 0

    def test_warns_when_sprint_flag_no_artifacts(self, tmp_path):
        sid = _unique_session()
        _make_zf(tmp_path)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        cache.set_flag("intent-sprint-flag", sid)
        r = _run(tmp_path, session_id=sid)
        assert r.returncode == 0
        assert "sprint intent" in r.stdout.lower() or "sprint intent" in r.stderr.lower(), (
            "must warn about sprint intent without approved artifacts"
        )

    def test_silent_when_sprint_flag_and_approved_spec(self, tmp_path):
        sid = _unique_session()
        zf = _make_zf(tmp_path)
        _approved_spec(zf)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        cache.set_flag("intent-sprint-flag", sid)
        r = _run(tmp_path, session_id=sid)
        assert r.returncode == 0
        # With approved artifacts, no warning emitted
        output = r.stdout + r.stderr
        assert "sprint intent detected but no approved" not in output.lower()

    def test_silent_when_sprint_flag_and_approved_plan(self, tmp_path):
        sid = _unique_session()
        zf = _make_zf(tmp_path)
        _approved_plan(zf)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        cache.set_flag("intent-sprint-flag", sid)
        r = _run(tmp_path, session_id=sid)
        assert r.returncode == 0
        output = r.stdout + r.stderr
        assert "sprint intent detected but no approved" not in output.lower()

    def test_deletes_sprint_flag_after_check(self, tmp_path):
        sid = _unique_session()
        _make_zf(tmp_path)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        cache.set_flag("intent-sprint-flag", sid)
        _run(tmp_path, session_id=sid)
        # Flag should be deleted — fresh CacheManager reads from disk
        fresh_cache = CacheManager(tmp_path / ".zie" / "cache")
        assert not fresh_cache.has_flag("intent-sprint-flag", sid)

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
            input="not json",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
