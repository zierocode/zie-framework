"""Tests for hooks/stop-handler.py — compact-hint merged into stop-handler (v1.29.0)."""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "stop-handler.py")


def _clean_tier_flags(cwd_path: Path, session_id: str = "nosid") -> None:
    """Delete any stale compact tier flags for this project + session."""
    safe_project = re.sub(r"[^a-zA-Z0-9]", "-", cwd_path.name)
    safe_sid = re.sub(r"[^a-zA-Z0-9]", "-", session_id) if session_id else "nosid"
    tmp = Path(tempfile.gettempdir())
    for tier in ("advisory", "mandatory"):
        flag = tmp / f"zie-{safe_project}-compact-tier-{tier}-{safe_sid}"
        flag.unlink(missing_ok=True)


def run_hook(tmp_cwd, event=None, config=None, env_overrides=None):
    if event is None:
        event = {}
    env = {**os.environ, "CLAUDE_CWD": str(tmp_cwd)}
    if env_overrides:
        env.update(env_overrides)
    if config is not None:
        zf = Path(tmp_cwd) / "zie-framework"
        zf.mkdir(parents=True, exist_ok=True)
        (zf / ".config").write_text(json.dumps(config))
    # Clean stale tier flags so each test starts fresh
    sid = event.get("session_id", "") if isinstance(event, dict) else ""
    _clean_tier_flags(Path(tmp_cwd), sid)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def make_cwd(tmp_path):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True, exist_ok=True)
    # Initialize as a git repo so stop-handler's uncommitted-file check
    # sees an empty repo instead of the real repo's uncommitted files.
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, timeout=5)
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True, timeout=5)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(tmp_path),
        capture_output=True,
        timeout=5,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@test.com",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@test.com",
        },
    )
    return tmp_path


class TestAdvisoryHint:
    def test_advisory_hint_at_80_pct(self, tmp_path):
        """80% — above advisory threshold (75%) → advisory hint appears."""
        cwd = make_cwd(tmp_path)
        event = {"context_window": {"current_tokens": 800, "max_tokens": 1000}}
        r = run_hook(cwd, event=event)
        assert r.returncode == 0
        assert "[zf] compact" in r.stdout.lower() or "Context at 80%" in r.stdout

    def test_advisory_hint_at_exactly_threshold(self, tmp_path):
        """Boundary: event at exactly 75% → advisory hint printed (>= not >)."""
        cwd = make_cwd(tmp_path)
        event = {"context_window": {"current_tokens": 750, "max_tokens": 1000}}
        r = run_hook(cwd, event=event)
        assert r.returncode == 0
        assert "[zf] compact" in r.stdout.lower() or "Context at 75%" in r.stdout


class TestNoHint:
    def test_no_hint_when_below_advisory_threshold(self, tmp_path):
        """Event at 70% — below advisory threshold (75%) → no stdout output."""
        cwd = make_cwd(tmp_path)
        event = {"context_window": {"current_tokens": 700, "max_tokens": 1000}}
        r = run_hook(cwd, event=event)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_graceful_skip_when_context_window_missing(self, tmp_path):
        """Event with no context_window field → exit 0, no stdout."""
        cwd = make_cwd(tmp_path)
        event = {"session_id": "abc123"}
        r = run_hook(cwd, event=event)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_graceful_skip_when_tokens_missing(self, tmp_path):
        """context_window present but empty dict → exit 0, no stdout."""
        cwd = make_cwd(tmp_path)
        event = {"context_window": {}}
        r = run_hook(cwd, event=event)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_stop_hook_active_guard(self, tmp_path):
        """stop_hook_active=true → exit 0 immediately, no hint."""
        cwd = make_cwd(tmp_path)
        event = {
            "stop_hook_active": True,
            "context_window": {"current_tokens": 950, "max_tokens": 1000},
        }
        r = run_hook(cwd, event=event)
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestThresholdConfig:
    def test_advisory_and_mandatory_thresholds_configurable(self, tmp_path):
        """Both thresholds configurable via .config."""
        cwd = make_cwd(tmp_path)
        config = {"compact_advisory_threshold": 0.90, "compact_mandatory_threshold": 0.95}

        # 85% — below custom advisory (90%) → no hint
        event_85 = {"context_window": {"current_tokens": 850, "max_tokens": 1000}}
        r85 = run_hook(cwd, event=event_85, config=config)
        assert r85.returncode == 0
        assert r85.stdout.strip() == ""

        # 91% — above custom advisory (90%) → advisory hint
        event_91 = {"context_window": {"current_tokens": 910, "max_tokens": 1000}}
        r91 = run_hook(cwd, event=event_91, config=config)
        assert r91.returncode == 0
        assert "[zf] Context at 91%" in r91.stdout


class TestAlwaysExitsZero:
    def test_always_exits_zero_when_hint_printed(self, tmp_path):
        """Even when hint is printed, exit code must be 0."""
        cwd = make_cwd(tmp_path)
        event = {"context_window": {"current_tokens": 900, "max_tokens": 1000}}
        r = run_hook(cwd, event=event)
        assert r.returncode == 0

    def test_always_exits_zero_on_malformed_stdin(self, tmp_path):
        """Malformed JSON stdin → outer guard exits 0."""
        make_cwd(tmp_path)
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, HOOK],
            input="not valid json{{",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestHooksJsonRegistration:
    def test_stop_handler_registered_in_hooks_json(self):
        """stop-handler.py (merged compact-hint v1.29.0) must be first Stop hook."""
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        stop_entries = data.get("hooks", {}).get("Stop", [])
        commands = [
            h["command"] for entry in stop_entries for h in entry.get("hooks", []) if h.get("type") == "command"
        ]
        # stop-handler.py must be first (fires before stop-capture, session-learn, etc.)
        assert len(commands) > 0, "Stop event must have at least one hook"
        assert "stop-handler.py" in commands[0], "stop-handler.py must be the first Stop hook; got: " + commands[0]
