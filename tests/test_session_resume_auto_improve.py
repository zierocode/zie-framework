#!/usr/bin/env python3
"""Unit tests for session-resume auto-improve functionality."""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def test_repo():
    """Create a minimal git repo for testing."""
    tmp = Path(tempfile.mkdtemp())
    os.chdir(tmp)
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], check=True, capture_output=True)

    # Create minimal zie-framework structure
    zf = tmp / "zie-framework"
    zf.mkdir()
    (zf / "ROADMAP.md").write_text("""# ROADMAP

## Next

## Ready

## Now

## Done
""")
    (zf / "backlog").mkdir()
    (zf / "specs").mkdir()
    (zf / "plans").mkdir()
    (zf / "memory").mkdir()
    (zf / "decisions").mkdir()

    # Create MEMORY.md
    (zf / "memory" / "MEMORY.md").write_text("""# Project Memory

## Context

Test project memory.

## References

- None
""")

    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


class TestSessionResumeAutoImprove:
    """Test session-resume auto-improve functionality."""

    def test_hook_file_exists(self):
        """session-resume.py exists."""
        hooks_dir = Path(__file__).parent.parent / "hooks"
        assert (hooks_dir / "session-resume.py").exists()

    def test_hook_registered(self):
        """session-resume registered in hooks.json for SessionStart."""
        hooks_json_path = Path(__file__).parent.parent / "hooks" / "hooks.json"
        hooks_json = json.loads(hooks_json_path.read_text())
        session_start_hooks = hooks_json.get("hooks", {}).get("SessionStart", [])

        assert len(session_start_hooks) > 0
        hook_commands = [h["hooks"][0]["command"] for h in session_start_hooks]
        assert any("session-resume.py" in cmd for cmd in hook_commands)

    def test_auto_apply_high_confidence_patterns(self, test_repo):
        """High-confidence patterns (>0.95) are auto-applied."""
        hook = Path(__file__).parent.parent / "hooks" / "session-resume.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-auto-improve-001"

        # Create session memory with high-confidence patterns
        zf = test_repo / "zie-framework"
        memory_file = zf / "memory" / "session-20260414-120000.json"
        memory_file.write_text(json.dumps({
            "session_id": "test-session-001",
            "timestamp": {"start": "2026-04-14T12:00:00Z", "end": "2026-04-14T12:30:00Z"},
            "patterns": [
                {
                    "id": "workflow-20260414-001",
                    "category": "workflow",
                    "description": "TDD loop: Read → Edit → Bash test",
                    "confidence": 0.96,
                    "auto_apply": True,
                    "frequency": 5,
                },
                {
                    "id": "decision-20260414-001",
                    "category": "decision",
                    "description": "Use atomic writes for all file operations",
                    "confidence": 0.98,
                    "auto_apply": True,
                    "frequency": 3,
                },
                {
                    "id": "workflow-20260414-002",
                    "category": "workflow",
                    "description": "Low confidence pattern",
                    "confidence": 0.80,
                    "auto_apply": False,
                    "frequency": 2,
                }
            ]
        }))

        result = subprocess.run(
            ["python3", str(hook)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input="{}",  # Empty event JSON
        )

        assert result.returncode == 0
        # Should output additionalContext with auto-applied patterns
        assert "additionalContext" in result.stdout
        assert "Auto-Improve" in result.stdout
        assert "TDD loop" in result.stdout or "atomic writes" in result.stdout

    def test_pattern_added_to_memory(self, test_repo):
        """Auto-applied patterns are added to MEMORY.md."""
        hook = Path(__file__).parent.parent / "hooks" / "session-resume.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-memory-001"

        zf = test_repo / "zie-framework"
        memory_file = zf / "memory" / "session-20260414-120000.json"
        memory_file.write_text(json.dumps({
            "session_id": "test-session-001",
            "timestamp": {"start": "2026-04-14T12:00:00Z", "end": "2026-04-14T12:30:00Z"},
            "patterns": [
                {
                    "id": "workflow-20260414-001",
                    "category": "workflow",
                    "description": "TDD loop: Read → Edit → Bash test",
                    "confidence": 0.96,
                    "auto_apply": True,
                    "frequency": 5,
                }
            ]
        }))

        subprocess.run(
            ["python3", str(hook)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input="{}",  # Empty event JSON
        )

        # Check MEMORY.md was updated
        memory_md = zf / "memory" / "MEMORY.md"
        content = memory_md.read_text()
        assert "## Patterns" in content
        assert "TDD loop" in content
        assert "WORKFLOW" in content

    def test_pending_learn_marker_cleanup(self, test_repo):
        """pending_learn.txt marker is cleaned up after processing."""
        hook = Path(__file__).parent.parent / "hooks" / "session-resume.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-cleanup-001"

        zf = test_repo / "zie-framework"
        marker = zf / "pending_learn.txt"
        marker.write_text("project=test\nwip=feature-x\n")

        subprocess.run(
            ["python3", str(hook)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input="{}",  # Empty event JSON
        )

        # Marker should be deleted
        assert not marker.exists()

    def test_wip_context_injection(self, test_repo):
        """WIP context from pending_learn.txt is injected."""
        hook = Path(__file__).parent.parent / "hooks" / "session-resume.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-wip-001"

        zf = test_repo / "zie-framework"
        marker = zf / "pending_learn.txt"
        marker.write_text("project=test\nwip=implementing auto-learn feature\n")

        result = subprocess.run(
            ["python3", str(hook)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input="{}",  # Empty event JSON
        )

        assert result.returncode == 0
        assert "WIP from last session" in result.stdout or "auto-learn" in result.stdout

    def test_no_patterns_no_output(self, test_repo):
        """No additionalContext output when no patterns to apply."""
        hook = Path(__file__).parent.parent / "hooks" / "session-resume.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-nopattern-001"

        result = subprocess.run(
            ["python3", str(hook)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
        )

        assert result.returncode == 0
        # Should not output additionalContext for auto-improve
        assert "additionalContext" not in result.stdout or "Auto-Improve" not in result.stdout

    def test_low_confidence_patterns_not_applied(self, test_repo):
        """Patterns below 0.95 threshold are not auto-applied."""
        hook = Path(__file__).parent.parent / "hooks" / "session-resume.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-lowconf-001"

        zf = test_repo / "zie-framework"
        memory_file = zf / "memory" / "session-20260414-120000.json"
        memory_file.write_text(json.dumps({
            "session_id": "test-session-001",
            "timestamp": {"start": "2026-04-14T12:00:00Z", "end": "2026-04-14T12:30:00Z"},
            "patterns": [
                {
                    "id": "workflow-20260414-001",
                    "category": "workflow",
                    "description": "Low confidence pattern",
                    "confidence": 0.90,
                    "auto_apply": False,
                    "frequency": 3,
                }
            ]
        }))

        result = subprocess.run(
            ["python3", str(hook)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
        )

        assert result.returncode == 0
        # Low confidence patterns should not be applied
        assert "additionalContext" not in result.stdout or "Auto-Improve" not in result.stdout

    def test_non_auto_apply_categories_not_applied(self, test_repo):
        """Patterns in non-auto-apply categories are not applied."""
        hook = Path(__file__).parent.parent / "hooks" / "session-resume.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-cat-001"

        zf = test_repo / "zie-framework"
        memory_file = zf / "memory" / "session-20260414-120000.json"
        memory_file.write_text(json.dumps({
            "session_id": "test-session-001",
            "timestamp": {"start": "2026-04-14T12:00:00Z", "end": "2026-04-14T12:30:00Z"},
            "patterns": [
                {
                    "id": "code-20260414-001",
                    "category": "code",
                    "description": "High confidence code pattern",
                    "confidence": 0.97,
                    "auto_apply": True,
                    "frequency": 5,
                }
            ]
        }))

        result = subprocess.run(
            ["python3", str(hook)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
        )

        assert result.returncode == 0
        # Code category is not in auto-apply categories
        assert "additionalContext" not in result.stdout or "Auto-Improve" not in result.stdout

    def test_empty_memory_dir_graceful(self, test_repo):
        """Empty memory directory handled gracefully."""
        hook = Path(__file__).parent.parent / "hooks" / "session-resume.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-empty-001"

        zf = test_repo / "zie-framework"
        # Memory dir exists but is empty
        memory_dir = zf / "memory"
        for f in memory_dir.glob("*.json"):
            f.unlink()

        result = subprocess.run(
            ["python3", str(hook)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
        )

        assert result.returncode == 0

    def test_corrupt_session_memory_graceful(self, test_repo):
        """Corrupt session memory files handled gracefully."""
        hook = Path(__file__).parent.parent / "hooks" / "session-resume.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-corrupt-001"

        zf = test_repo / "zie-framework"
        memory_file = zf / "memory" / "session-20260414-120000.json"
        memory_file.write_text("not valid json {{{")

        result = subprocess.run(
            ["python3", str(hook)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
        )

        assert result.returncode == 0
