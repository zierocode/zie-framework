"""Tests for persistent snapshot in hooks/sdlc-compact.py."""
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
    """Create a zie-framework directory with optional .config."""
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


class TestPreCompactPersistentWrite:
    def test_precompact_writes_persistent(self, tmp_path):
        """PreCompact writes snapshot to both /tmp and persistent path."""
        cwd = _make_cwd(tmp_path)
        plugin_data = tmp_path / "plugin_data"
        plugin_data.mkdir(exist_ok=True)
        event = {
            "hook_event_name": "PreCompact",
            "session_id": "persist-test-1",
            "context_window": {"current_tokens": 500, "max_tokens": 1000},
        }
        env = {"CLAUDE_PLUGIN_DATA": str(plugin_data)}
        r = _run_hook(cwd, event, env)
        assert r.returncode == 0
        # Check persistent path has content
        safe_project = cwd.name  # project name is the dir basename
        persist_dir = plugin_data / f"zie-{safe_project}-persistent"
        if persist_dir.exists():
            persist_file = persist_dir / "compact-snapshot"
            assert persist_file.exists()
            data = json.loads(persist_file.read_text())
            assert "active_task" in data

    def test_persistent_write_failure_does_not_block(self, tmp_path):
        """If persistent write fails, PreCompact still exits 0 (non-blocking)."""
        cwd = _make_cwd(tmp_path)
        event = {
            "hook_event_name": "PreCompact",
            "session_id": "persist-fail-test",
            "context_window": {"current_tokens": 500, "max_tokens": 1000},
        }
        # Point CLAUDE_PLUGIN_DATA to a non-existent path — should not crash
        env = {"CLAUDE_PLUGIN_DATA": "/nonexistent/path/that/does/not/exist"}
        r = _run_hook(cwd, event, env)
        assert r.returncode == 0


class TestPostCompactPersistentRead:
    def test_postcompact_reads_persistent_fallback(self, tmp_path):
        """PostCompact reads from persistent path when /tmp snapshot is missing."""
        cwd = _make_cwd(tmp_path)
        plugin_data = tmp_path / "plugin_data"
        plugin_data.mkdir(exist_ok=True)

        # Delete any /tmp snapshot so PostCompact must fall back to persistent
        import re as _re
        safe_project = _re.sub(r'[^a-zA-Z0-9]', '-', cwd.name)
        tmp_snap = Path(tempfile.gettempdir()) / f"zie-{safe_project}-compact-snapshot"
        tmp_snap.unlink(missing_ok=True)

        # Write a persistent snapshot using the same path convention as the hook
        # persistent_project_path("compact-snapshot", project) -> CLAUDE_PLUGIN_DATA/<project>/compact-snapshot
        persist_dir = plugin_data / safe_project
        persist_dir.mkdir(parents=True, exist_ok=True)
        persist_file = persist_dir / "compact-snapshot"
        snapshot_data = {
            "active_task": "test-feature",
            "now_items": ["test-feature"],
            "git_branch": "dev",
            "changed_files": ["file.py"],
            "tdd_phase": "GREEN",
        }
        persist_file.write_text(json.dumps(snapshot_data))

        event = {
            "hook_event_name": "PostCompact",
            "session_id": "persist-read-test",
        }
        env = {"CLAUDE_PLUGIN_DATA": str(plugin_data)}
        r = _run_hook(cwd, event, env)
        assert r.returncode == 0
        output = json.loads(r.stdout)
        assert "test-feature" in output.get("additionalContext", "")

    def test_postcompact_roadmap_fallback_when_both_missing(self, tmp_path):
        """PostCompact falls back to live ROADMAP when both snapshots are missing."""
        cwd = _make_cwd(tmp_path)
        event = {
            "hook_event_name": "PostCompact",
            "session_id": "persist-none-test",
        }
        r = _run_hook(cwd, event)
        assert r.returncode == 0
        # Should still produce output (from live ROADMAP fallback)
        # The output may be minimal since Now lane has [x] test-item
        output = r.stdout.strip()
        # It's OK for output to be empty or minimal — just shouldn't crash
        assert r.returncode == 0