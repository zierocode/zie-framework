"""Tests for 2-tier context window health in hooks/stop-handler.py (compact-hint merged v1.29.0)."""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "stop-handler.py"


def _flag(project: str, name: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9]", "-", project)
    return Path(tempfile.gettempdir()) / f"zie-{safe}-{name}"


def _clean_nudge_cache(session_id: str) -> None:
    """Clean nudge-check cache for a session."""
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "-", session_id)
    cache_dir = Path(tempfile.gettempdir()) / f"zie-{safe_id}"
    if cache_dir.exists():
        for cache_file in cache_dir.glob("git-*.cache"):
            cache_file.unlink(missing_ok=True)
        cache_dir.rmdir()  # Remove dir if empty


def run_hook(
    tmp_path: Path, current: int, maximum: int = 1000, session_id: str = "test-tiers"
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    env["CLAUDE_SESSION_ID"] = session_id
    # Setup zie-framework dir so config loads
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    # Create .config with threshold settings
    config = {
        "compact_advisory_threshold": 0.75,
        "compact_mandatory_threshold": 0.90,
    }
    (zf / ".config").write_text(json.dumps(config))
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
        _clean_nudge_cache(session_id)

    def test_fires_at_75_pct(self, tmp_path):
        self._clean(tmp_path, "tier75-a")
        r = run_hook(tmp_path, current=750, maximum=1000, session_id="tier75-a")
        assert r.returncode == 0
        assert "Context at 75%" in r.stdout, f"Expected 75% hint in stdout: {r.stdout!r}"
        assert "compact" in r.stdout.lower()
        self._clean(tmp_path, "tier75-a")

    def test_no_output_at_74_pct(self, tmp_path):
        self._clean(tmp_path, "tier75-b")
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
        assert "Context at 75%" in r1.stdout or "Context at 78%" in r1.stdout
        # Second run same session: advisory tier already fired, should not nag again
        assert r1.returncode == 0
        assert r2.returncode == 0
        # Second run should be silent at the advisory level (mandatory still fires at 90%+)
        assert "Context at 75%" not in r2.stdout and "Context at 78%" not in r2.stdout
        self._clean(tmp_path, sid)


class TestMandatoryTier90:
    """90% mandatory tier: hard warning (existing behavior preserved)."""

    def _clean(self, tmp_path: Path, sid: str) -> None:
        for name in ("compact-tier-advisory", "compact-tier-mandatory"):
            _flag(tmp_path.name, f"{name}-{sid}").unlink(missing_ok=True)
        _clean_nudge_cache(sid)

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
        # Mandatory tier message should mention fresh session
        assert "fresh session" in r.stdout.lower()
        self._clean(tmp_path, sid)
