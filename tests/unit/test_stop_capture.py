"""Unit tests for hooks/stop-capture.py (Area 1 — Conversation Capture)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "stop-capture.py"
sys.path.insert(0, str(REPO_ROOT / "hooks"))
from utils_cache import CacheManager


def _run(tmp_path: Path, session_id: str = "test-session") -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"session_id": session_id, "stop_reason": "end_turn"})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event,
        capture_output=True,
        text=True,
        env=env,
    )


def _get_cache(tmp_path: Path, session_id: str = "test-session") -> CacheManager:
    return CacheManager(tmp_path / ".zie" / "cache")


class TestStopCapture:
    def test_skips_write_when_brainstorm_active(self, tmp_path):
        (tmp_path / "zie-framework").mkdir(parents=True)
        cache = _get_cache(tmp_path)
        cache.set_flag("brainstorm-active", "test-session")
        cache.set_flag("design-mode", "test-session")
        r = _run(tmp_path)
        assert r.returncode == 0
        handoff = tmp_path / ".zie" / "handoff.md"
        assert not handoff.exists(), "must skip write when brainstorm-active flag present"

    def test_skips_write_when_no_design_mode_flag(self, tmp_path):
        (tmp_path / "zie-framework").mkdir(parents=True)
        r = _run(tmp_path)
        assert r.returncode == 0
        handoff = tmp_path / ".zie" / "handoff.md"
        assert not handoff.exists(), "must skip write when design-mode flag absent"

    def test_writes_handoff_when_design_mode_active(self, tmp_path):
        (tmp_path / "zie-framework").mkdir(parents=True)
        cache = _get_cache(tmp_path)
        cache.set_flag("design-mode", "test-session")
        r = _run(tmp_path)
        assert r.returncode == 0
        handoff = tmp_path / ".zie" / "handoff.md"
        assert handoff.exists(), "must write .zie/handoff.md when design-mode flag set"

    def test_handoff_has_correct_frontmatter(self, tmp_path):
        (tmp_path / "zie-framework").mkdir(parents=True)
        cache = _get_cache(tmp_path)
        cache.set_flag("design-mode", "test-session")
        _run(tmp_path)
        content = (tmp_path / ".zie" / "handoff.md").read_text()
        assert "captured_at:" in content
        assert "source: design-tracker" in content

    def test_deletes_design_mode_flag_after_write(self, tmp_path):
        (tmp_path / "zie-framework").mkdir(parents=True)
        cache = _get_cache(tmp_path)
        cache.set_flag("design-mode", "test-session")
        _run(tmp_path)
        # Flag should be deleted — fresh CacheManager reads from disk
        fresh_cache = CacheManager(tmp_path / ".zie" / "cache")
        assert not fresh_cache.has_flag("design-mode", "test-session")

    def test_handoff_has_required_sections(self, tmp_path):
        (tmp_path / "zie-framework").mkdir(parents=True)
        cache = _get_cache(tmp_path)
        cache.set_flag("design-mode", "test-session")
        _run(tmp_path)
        content = (tmp_path / ".zie" / "handoff.md").read_text()
        for section in ("## Goals", "## Key Decisions", "## Next Step"):
            assert section in content, f"handoff.md must contain '{section}'"

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
