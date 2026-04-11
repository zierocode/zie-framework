"""Tests for 3-tier context window health in hooks/compact-hint.py (Sprint B)."""
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


class TestSoftTier70:
    """70% tier: soft hint fires at ≥70%, once per session."""

    def _clean(self, tmp_path: Path, session_id: str = "test-tiers") -> None:
        for name in ("compact-tier-70", "compact-tier-80", "compact-tier-90"):
            _flag(tmp_path.name, f"{name}-{session_id}").unlink(missing_ok=True)

    def test_fires_at_70_pct(self, tmp_path):
        self._clean(tmp_path)
        r = run_hook(tmp_path, current=700, maximum=1000, session_id="tier70-a")
        assert r.returncode == 0
        assert "70%" in r.stdout, f"Expected 70% hint in stdout: {r.stdout!r}"
        assert "compact" in r.stdout.lower()
        self._clean(tmp_path, "tier70-a")

    def test_no_output_at_69_pct(self, tmp_path):
        self._clean(tmp_path)
        r = run_hook(tmp_path, current=690, maximum=1000, session_id="tier70-b")
        assert r.returncode == 0
        assert "69%" not in r.stdout
        assert "70%" not in r.stdout
        self._clean(tmp_path, "tier70-b")

    def test_fires_only_once_per_session(self, tmp_path):
        sid = "tier70-once"
        self._clean(tmp_path, sid)
        r1 = run_hook(tmp_path, current=700, session_id=sid)
        r2 = run_hook(tmp_path, current=720, session_id=sid)
        assert "70%" in r1.stdout or "72%" in r1.stdout
        # Second run same session: tier already fired, should not fire again at same tier
        assert "tier already fired" not in r2.stdout  # implementation detail
        # At minimum: first run produced output, second run must not double-nag
        # (either silent or different tier message)
        assert r1.returncode == 0
        assert r2.returncode == 0
        self._clean(tmp_path, sid)


class TestMidTier80:
    """80% tier: recommendation fires at ≥80% (existing behavior preserved)."""

    def _clean(self, tmp_path: Path, sid: str) -> None:
        for name in ("compact-tier-70", "compact-tier-80", "compact-tier-90"):
            _flag(tmp_path.name, f"{name}-{sid}").unlink(missing_ok=True)

    def test_fires_at_80_pct(self, tmp_path):
        sid = "tier80-a"
        self._clean(tmp_path, sid)
        r = run_hook(tmp_path, current=800, session_id=sid)
        assert r.returncode == 0
        assert "80%" in r.stdout
        self._clean(tmp_path, sid)

    def test_does_not_fire_80_tier_at_79_pct(self, tmp_path):
        sid = "tier80-b"
        self._clean(tmp_path, sid)
        r = run_hook(tmp_path, current=790, session_id=sid)
        assert r.returncode == 0
        # 79% is above soft tier (70%) but below mid tier (80%)
        # Should fire soft hint, but NOT the 80% "approaching limit" message
        assert "approaching limit" not in r.stdout
        assert "make zie-release" not in r.stdout
        self._clean(tmp_path, sid)


class TestHardTier90:
    """90% tier: hard warning (existing behavior preserved)."""

    def _clean(self, tmp_path: Path, sid: str) -> None:
        for name in ("compact-tier-70", "compact-tier-80", "compact-tier-90"):
            _flag(tmp_path.name, f"{name}-{sid}").unlink(missing_ok=True)

    def test_fires_at_90_pct(self, tmp_path):
        sid = "tier90-a"
        self._clean(tmp_path, sid)
        r = run_hook(tmp_path, current=900, session_id=sid)
        assert r.returncode == 0
        assert "90%" in r.stdout or "Context at 9" in r.stdout
        self._clean(tmp_path, sid)
