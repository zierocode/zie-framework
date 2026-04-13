"""Tests for PostCompact sprint guard in hooks/sdlc-compact.py."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "sdlc-compact.py"


def _make_cwd(tmp_path: Path, config: dict | None = None) -> Path:
    """Create a zie-framework directory with ROADMAP and optional .config."""
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    (zf / "ROADMAP.md").write_text("# ROADMAP\n\n## Now\n\n- [x] test-item\n\n## Done\n")
    if config:
        (zf / ".config").write_text(json.dumps(config))
    return tmp_path


def _run_hook(tmp_path: Path, event: dict, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


class TestSprintGuardInjected:
    def test_sprint_guard_injected_when_state_exists(self, tmp_path):
        """When .sprint-state exists, PostCompact output includes SPRINT ACTIVE."""
        cwd = _make_cwd(tmp_path)
        zf = tmp_path / "zie-framework"
        # Write sprint state
        state = {
            "phase": 2,
            "remaining_items": ["item-b", "item-c"],
            "current_task": "item-a",
            "tdd_phase": "GREEN",
            "last_action": "impl-start",
            "started_at": "2026-04-13T10:00:00",
        }
        (zf / ".sprint-state").write_text(json.dumps(state))

        event = {
            "hook_event_name": "PostCompact",
            "session_id": "sprint-guard-1",
        }
        r = _run_hook(cwd, event)
        assert r.returncode == 0
        output = json.loads(r.stdout)
        ctx = output.get("additionalContext", "")
        assert "SPRINT ACTIVE" in ctx
        assert "Phase 2" in ctx
        assert "item-a" in ctx
        assert "GREEN" in ctx

    def test_sprint_guard_skipped_when_no_state(self, tmp_path):
        """No .sprint-state file means no SPRINT ACTIVE in output."""
        cwd = _make_cwd(tmp_path)
        event = {
            "hook_event_name": "PostCompact",
            "session_id": "sprint-guard-2",
        }
        r = _run_hook(cwd, event)
        assert r.returncode == 0
        output = json.loads(r.stdout)
        ctx = output.get("additionalContext", "")
        assert "SPRINT ACTIVE" not in ctx

    def test_sprint_guard_handles_malformed_state(self, tmp_path):
        """Malformed .sprint-state → hook exits 0 and logs error, no SPRINT ACTIVE."""
        cwd = _make_cwd(tmp_path)
        zf = tmp_path / "zie-framework"
        (zf / ".sprint-state").write_text("{invalid json")
        event = {
            "hook_event_name": "PostCompact",
            "session_id": "sprint-guard-3",
        }
        r = _run_hook(cwd, event)
        assert r.returncode == 0
        # SPRINT ACTIVE should NOT appear (JSON parse failed, guard caught it)
        output = json.loads(r.stdout)
        ctx = output.get("additionalContext", "")
        assert "SPRINT ACTIVE" not in ctx

    def test_sprint_guard_includes_remaining_count(self, tmp_path):
        """SPRINT ACTIVE includes remaining items count."""
        cwd = _make_cwd(tmp_path)
        zf = tmp_path / "zie-framework"
        state = {
            "phase": 3,
            "remaining_items": ["item-x", "item-y", "item-z"],
            "current_task": "release",
            "tdd_phase": "",
            "last_action": "release-start",
            "started_at": "2026-04-13T10:00:00",
        }
        (zf / ".sprint-state").write_text(json.dumps(state))
        event = {
            "hook_event_name": "PostCompact",
            "session_id": "sprint-guard-4",
        }
        r = _run_hook(cwd, event)
        assert r.returncode == 0
        output = json.loads(r.stdout)
        ctx = output.get("additionalContext", "")
        assert "3 items remaining" in ctx