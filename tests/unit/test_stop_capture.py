"""Unit tests for hooks/stop-capture.py (Area 1 — Conversation Capture)."""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "stop-capture.py"


def _flag(project: str, name: str) -> Path:
    safe = re.sub(r'[^a-zA-Z0-9]', '-', project)
    return Path(tempfile.gettempdir()) / f"zie-{safe}-{name}"


def _run(tmp_path: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"session_id": "test-session", "stop_reason": "end_turn"})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event,
        capture_output=True,
        text=True,
        env=env,
    )


class TestStopCapture:
    def test_skips_write_when_brainstorm_active(self, tmp_path):
        project = tmp_path.name
        _flag(project, "brainstorm-active").write_text("active")
        _flag(project, "design-mode").write_text("active")
        r = _run(tmp_path)
        assert r.returncode == 0
        handoff = tmp_path / ".zie" / "handoff.md"
        assert not handoff.exists(), "must skip write when brainstorm-active flag present"
        _flag(project, "brainstorm-active").unlink(missing_ok=True)
        _flag(project, "design-mode").unlink(missing_ok=True)

    def test_skips_write_when_no_design_mode_flag(self, tmp_path):
        r = _run(tmp_path)
        assert r.returncode == 0
        handoff = tmp_path / ".zie" / "handoff.md"
        assert not handoff.exists(), "must skip write when design-mode flag absent"

    def test_writes_handoff_when_design_mode_active(self, tmp_path):
        project = tmp_path.name
        _flag(project, "design-mode").write_text("active")
        r = _run(tmp_path)
        assert r.returncode == 0
        handoff = tmp_path / ".zie" / "handoff.md"
        assert handoff.exists(), "must write .zie/handoff.md when design-mode flag set"
        _flag(project, "design-mode").unlink(missing_ok=True)

    def test_handoff_has_correct_frontmatter(self, tmp_path):
        project = tmp_path.name
        _flag(project, "design-mode").write_text("active")
        _run(tmp_path)
        content = (tmp_path / ".zie" / "handoff.md").read_text()
        assert "captured_at:" in content
        assert "source: design-tracker" in content
        _flag(project, "design-mode").unlink(missing_ok=True)

    def test_deletes_design_mode_flag_after_write(self, tmp_path):
        project = tmp_path.name
        flag = _flag(project, "design-mode")
        flag.write_text("active")
        _run(tmp_path)
        assert not flag.exists(), "design-mode flag must be deleted after handoff write"

    def test_handoff_has_required_sections(self, tmp_path):
        project = tmp_path.name
        _flag(project, "design-mode").write_text("active")
        _run(tmp_path)
        content = (tmp_path / ".zie" / "handoff.md").read_text()
        for section in ("## Goals", "## Key Decisions", "## Next Step"):
            assert section in content, f"handoff.md must contain '{section}'"
        _flag(project, "design-mode").unlink(missing_ok=True)

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
