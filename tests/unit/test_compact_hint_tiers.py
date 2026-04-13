"""Tests for 2-tier context window health in hooks/compact-hint.py."""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "compact-hint.py"


def _flag(project: str, name: str) -> Path:
    safe = re.sub(r'[^a-zA-Z0-9]', '-', project)
    return Path(tempfile.gettempdir()) / f"zie-{safe}-{name}"


def run_hook(tmp_path: Path, current: int, maximum: int = 1000,
             session_id: str = "test-tiers") -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    # Setup zie-framework dir so config loads
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    event = {
        "session_id": session_id,
        "context_window": {"current_tokens": current, "max_tokens": maximum},
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


class TestAdvisoryTier75:
    """75% advisory tier: gentle hint fires at ≥75%, once per session."""

    def _clean(self, tmp_path: Path, session_id: str = "test-tiers") -> None:
        for name in ("compact-tier-advisory", "compact-tier-mandatory"):
            _flag(tmp_path.name, f"{name}-{session_id}").unlink(missing_ok=True)

    def test_fires_at_75_pct(self, tmp_path):
        self._clean(tmp_path)
        r = run_hook(tmp_path, current=750, maximum=1000, session_id="tier75-a")
        assert r.returncode == 0
        assert "75%" in r.stdout, f"Expected 75% hint in stdout: {r.stdout!r}"
        assert "compact" in r.stdout.lower()
        self._clean(tmp_path, "tier75-a")

    def test_no_output_at_74_pct(self, tmp_path):
        self._clean(tmp_path)
        r = run_hook(tmp_path, current=740, maximum=1000, session_id="tier75-b")
        assert r.returncode == 0
        assert "74%" not in r.stdout
        assert "75%" not in r.stdout
        assert r.stdout.strip() == ""
        self._clean(tmp_path, "tier75-b")

    def test_fires_only_once_per_session(self, tmp_path):
        sid = "tier75-once"
        self._clean(tmp_path, sid)
        r1 = run_hook(tmp_path, current=750, session_id=sid)
        r2 = run_hook(tmp_path, current=780, session_id=sid)
        assert "75%" in r1.stdout or "78%" in r1.stdout
        # Second run same session: advisory tier already fired, should not nag again
        assert r1.returncode == 0
        assert r2.returncode == 0
        # Second run should be silent at the advisory level (mandatory still fires at 90%+)
        assert "75%" not in r2.stdout or "78%" not in r2.stdout or "consider" not in r2.stdout.lower()
        self._clean(tmp_path, sid)


class TestMandatoryTier90:
    """90% mandatory tier: hard warning (existing behavior preserved)."""

    def _clean(self, tmp_path: Path, sid: str) -> None:
        for name in ("compact-tier-advisory", "compact-tier-mandatory"):
            _flag(tmp_path.name, f"{name}-{sid}").unlink(missing_ok=True)

    def test_fires_at_90_pct(self, tmp_path):
        sid = "tier90-a"
        self._clean(tmp_path, sid)
        r = run_hook(tmp_path, current=900, session_id=sid)
        assert r.returncode == 0
        assert "90%" in r.stdout or "Context at 9" in r.stdout
        self._clean(tmp_path, sid)

    def test_mandatory_message_suggests_fresh_session(self, tmp_path):
        sid = "tier90-msg"
        self._clean(tmp_path, sid)
        r = run_hook(tmp_path, current=920, session_id=sid)
        assert r.returncode == 0
        # Mandatory tier message should mention starting fresh
        assert "fresh session" in r.stdout.lower() or "new session" in r.stdout.lower()
        self._clean(tmp_path, sid)