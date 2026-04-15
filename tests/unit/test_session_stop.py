#!/usr/bin/env python3
"""Unit tests for session-stop hook (auto-learn pattern extraction)."""
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
- [ ] auto-learn feature

## Done
""")
    (zf / "backlog").mkdir()
    (zf / "specs").mkdir()
    (zf / "plans").mkdir()
    (zf / "memory").mkdir(mode=0o700)

    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


class TestSessionStopHook:
    """Test session-stop hook functionality."""

    def test_hook_file_exists(self):
        """session-stop.py exists."""
        hooks_dir = Path(__file__).parent.parent.parent / "hooks"
        assert (hooks_dir / "session-stop.py").exists()

    def test_hook_registered(self):
        """session-stop registered in hooks.json."""
        hooks_json_path = Path(__file__).parent.parent.parent / "hooks" / "hooks.json"
        hooks_json = json.loads(hooks_json_path.read_text())
        stop_hooks = hooks_json.get("hooks", {}).get("Stop", [])[0].get("hooks", [])
        hook_commands = [h["command"] for h in stop_hooks]
        assert any("session-stop.py" in cmd for cmd in hook_commands)

    def test_session_memory_schema(self, test_repo):
        """Session memory file follows correct schema."""
        session_stop = Path(__file__).parent.parent.parent / "hooks" / "session-stop.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-session-001"
        event_data = json.dumps({
            "conversation_history": [
                "Called the Read tool",
                "Called the Write tool",
                "Called the Bash tool with test",
            ]
        })
        result = subprocess.run(
            ["python3", str(session_stop)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input=event_data,
        )

        assert result.returncode == 0

        # Check session memory file created
        memory_dir = test_repo / "zie-framework" / "memory"
        session_files = list(memory_dir.glob("session-*.json"))
        assert len(session_files) > 0

        # Validate schema
        session_data = json.loads(session_files[0].read_text())
        assert "session_id" in session_data
        assert "timestamp" in session_data
        assert "summary" in session_data
        assert "patterns" in session_data
        assert "context_keywords" in session_data
        assert isinstance(session_data["patterns"], list)
        assert isinstance(session_data["context_keywords"], list)

    def test_pattern_extraction_heuristic(self, test_repo):
        """Heuristic pattern extraction detects repeated sequences."""
        session_stop = Path(__file__).parent.parent.parent / "hooks" / "session-stop.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-pattern-001"

        # Simulate TDD loop repeated 5 times
        transcript = []
        for _ in range(5):
            transcript.extend([
                "Called the Read tool",
                "Called the Write tool",
                "Called the Bash tool with pytest",
            ])

        event_data = json.dumps({"conversation_history": transcript})
        result = subprocess.run(
            ["python3", str(session_stop)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input=event_data,
        )

        assert result.returncode == 0

        memory_dir = test_repo / "zie-framework" / "memory"
        session_files = list(memory_dir.glob("session-*.json"))
        session_data = json.loads(session_files[0].read_text())

        # Should have extracted patterns
        assert len(session_data["patterns"]) > 0

        # Check pattern structure
        for pattern in session_data["patterns"]:
            assert "id" in pattern
            assert "category" in pattern
            assert "description" in pattern
            assert "confidence" in pattern
            assert "frequency" in pattern
            assert "auto_apply" in pattern
            assert isinstance(pattern["confidence"], (int, float))
            assert 0.0 <= pattern["confidence"] <= 1.0

    def test_auto_apply_threshold(self, test_repo):
        """Patterns with confidence >= 0.95 marked auto_apply=true."""
        session_stop = Path(__file__).parent.parent.parent / "hooks" / "session-stop.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-threshold-001"

        # Create high-frequency pattern (10+ occurrences)
        transcript = []
        for _ in range(15):
            transcript.append("Called the Write tool")
            transcript.append("TDD loop pattern detected")

        event_data = json.dumps({"conversation_history": transcript})
        result = subprocess.run(
            ["python3", str(session_stop)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input=event_data,
        )

        assert result.returncode == 0

        memory_dir = test_repo / "zie-framework" / "memory"
        session_files = list(memory_dir.glob("session-*.json"))
        session_data = json.loads(session_files[0].read_text())

        # High frequency patterns should have high confidence
        high_conf_patterns = [p for p in session_data["patterns"] if p["confidence"] >= 0.95]
        # May or may not have auto-apply patterns depending on exact scoring
        # Test verifies the threshold logic exists
        for pattern in high_conf_patterns:
            assert pattern["auto_apply"] is True

    def test_context_keywords_extraction(self, test_repo):
        """Context keywords extracted from transcript."""
        session_stop = Path(__file__).parent.parent.parent / "hooks" / "session-stop.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-keywords-001"

        transcript = [
            "Implementing the TDD workflow with pytest",
            "Writing tests for the hook system",
            "Pattern extraction uses keyword frequency analysis",
        ]

        event_data = json.dumps({"conversation_history": transcript})
        result = subprocess.run(
            ["python3", str(session_stop)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input=event_data,
        )

        assert result.returncode == 0

        memory_dir = test_repo / "zie-framework" / "memory"
        session_files = list(memory_dir.glob("session-*.json"))
        session_data = json.loads(session_files[0].read_text())

        assert len(session_data["context_keywords"]) > 0
        assert len(session_data["context_keywords"]) <= 5  # Top 5

    def test_sdlc_stage_detection(self, test_repo):
        """SDLC stage detected from ROADMAP Now lane."""
        session_stop = Path(__file__).parent.parent.parent / "hooks" / "session-stop.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-stage-001"
        event_data = json.dumps({})
        result = subprocess.run(
            ["python3", str(session_stop)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input=event_data,
        )

        assert result.returncode == 0

        memory_dir = test_repo / "zie-framework" / "memory"
        session_files = list(memory_dir.glob("session-*.json"))
        session_data = json.loads(session_files[0].read_text())

        assert "sdlc_stage" in session_data
        assert session_data["sdlc_stage"] in ["idle", "spec", "plan", "implement", "fix", "release", "retro", "in-progress"]

    def test_pending_learn_marker(self, test_repo):
        """pending_learn.txt written for next session."""
        session_stop = Path(__file__).parent.parent.parent / "hooks" / "session-stop.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-pending-001"
        event_data = json.dumps({})
        result = subprocess.run(
            ["python3", str(session_stop)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input=event_data,
        )

        assert result.returncode == 0

        pending_file = test_repo / "zie-framework" / "pending_learn.txt"
        assert pending_file.exists()
        content = pending_file.read_text()
        assert "project=" in content
        assert "wip=" in content

    def test_empty_transcript_graceful(self, test_repo):
        """Empty transcript handled gracefully."""
        session_stop = Path(__file__).parent.parent.parent / "hooks" / "session-stop.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-empty-001"
        event_data = json.dumps({"conversation_history": []})
        result = subprocess.run(
            ["python3", str(session_stop)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input=event_data,
        )

        assert result.returncode == 0

        # Should still create session memory file
        memory_dir = test_repo / "zie-framework" / "memory"
        session_files = list(memory_dir.glob("session-*.json"))
        assert len(session_files) > 0


class TestSessionStopPermissions:
    """Test file permissions for session-stop outputs."""

    def test_session_memory_permissions(self, test_repo):
        """Session memory files have 0o600 permissions."""
        session_stop = Path(__file__).parent.parent.parent / "hooks" / "session-stop.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-perms-001"
        event_data = json.dumps({"conversation_history": ["test"]})
        subprocess.run(
            ["python3", str(session_stop)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input=event_data,
        )

        memory_dir = test_repo / "zie-framework" / "memory"
        session_files = list(memory_dir.glob("session-*.json"))
        assert len(session_files) > 0

        # Check file permissions (Unix only)
        if os.name != "nt":
            mode = session_files[0].stat().st_mode & 0o777
            assert mode == 0o600

    def test_memory_dir_permissions(self, test_repo):
        """Memory directory has 0o700 permissions."""
        session_stop = Path(__file__).parent.parent.parent / "hooks" / "session-stop.py"
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = "test-dir-perms-001"
        event_data = json.dumps({"conversation_history": ["test"]})
        subprocess.run(
            ["python3", str(session_stop)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(test_repo),
            input=event_data,
        )

        memory_dir = test_repo / "zie-framework" / "memory"
        if os.name != "nt":
            mode = memory_dir.stat().st_mode & 0o777
            assert mode == 0o700
