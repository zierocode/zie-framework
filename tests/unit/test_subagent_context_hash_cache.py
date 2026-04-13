"""Unit tests for content-hash dedup in subagent-context.py."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOKS_DIR = REPO_ROOT / "hooks"
HOOK = HOOKS_DIR / "subagent-context.py"


def _make_zf(tmp_path: Path, with_context: bool = True) -> None:
    zf = tmp_path / "zie-framework"
    zf.mkdir()
    (zf / ".config").write_text('{"project_type": "lib"}')
    (zf / "ROADMAP.md").write_text("## Now\n\n- active-feature\n\n## Next\n\n## Done\n")
    if with_context:
        decisions = zf / "decisions"
        decisions.mkdir(exist_ok=True)
        (decisions / "ADR-000-summary.md").write_text("# ADR Summary\n\n- ADR-001: Test decision\n")
        project = zf / "project"
        project.mkdir(exist_ok=True)
        (project / "context.md").write_text("## ADR-001\n\nSome context.\n")


def _run_hook(tmp_path: Path, agent_type: str,
              session_id: str = "test-session") -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"agentType": agent_type, "session_id": session_id})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event, capture_output=True, text=True, env=env,
    )


def _cache_flag(tmp_path: Path, session_id: str = "test-session") -> Path:
    project = tmp_path.name
    safe = project  # project name from tmp_path is already safe
    safe_sid = session_id  # test-session is already safe
    return Path(tempfile.gettempdir()) / f"zie-{safe}-session-context-{safe_sid}"


def _hash_file(tmp_path: Path) -> Path:
    """Return the path to the content-hash cache file for this project."""
    project = tmp_path.name
    # Use project_tmp_path convention: /tmp/zie-<project>-context-hash-<project>
    return Path(tempfile.gettempdir()) / f"zie-{project}-context-hash-{project}"


def _cleanup(tmp_path: Path, session_id: str = "test-session"):
    """Remove cache flag and hash file after a test."""
    _cache_flag(tmp_path, session_id).unlink(missing_ok=True)
    _hash_file(tmp_path).unlink(missing_ok=True)


class TestContentHashCache:
    """Content-hash cache skips re-injection when ADR summary + project context unchanged."""

    def test_writes_hash_file_on_inject(self, tmp_path):
        """First injection must write a content-hash cache file."""
        _make_zf(tmp_path)
        _cleanup(tmp_path)
        r = _run_hook(tmp_path, "Explore")
        assert r.returncode == 0
        hash_path = _hash_file(tmp_path)
        assert hash_path.exists(), "hash file must be written after injection"
        content = hash_path.read_text()
        lines = content.splitlines()
        assert len(lines) >= 2, "hash file must contain hash + timestamp"
        assert len(lines[0]) == 64, "SHA-256 hex digest must be 64 chars"
        # Timestamp should be a valid float
        float(lines[1])  # raises ValueError if not a valid timestamp
        _cleanup(tmp_path)

    def test_skips_inject_on_hash_hit_within_ttl(self, tmp_path):
        """When content hash matches and TTL not expired, skip injection."""
        _make_zf(tmp_path)
        _cleanup(tmp_path)

        # First inject to establish the hash
        r1 = _run_hook(tmp_path, "Explore", session_id="s1")
        assert r1.returncode == 0
        assert r1.stdout.strip(), "first inject should emit context"

        # Clean session flag so session cache doesn't interfere,
        # but leave hash file intact
        _cache_flag(tmp_path, "s1").unlink(missing_ok=True)

        # Second run with different session — should skip because hash matches
        r2 = _run_hook(tmp_path, "Explore", session_id="s2")
        assert r2.returncode == 0
        assert r2.stdout.strip() == "", "should skip injection on hash cache hit"
        _cleanup(tmp_path)

    def test_reinjects_after_ttl_expires(self, tmp_path):
        """When hash matches but TTL expired, must re-inject."""
        _make_zf(tmp_path)
        _cleanup(tmp_path)

        # First inject
        r1 = _run_hook(tmp_path, "Explore", session_id="s1")
        assert r1.stdout.strip(), "first inject should emit context"

        # Expire hash: write an old timestamp (> 600s ago)
        hash_path = _hash_file(tmp_path)
        stored_hash = hash_path.read_text().splitlines()[0]
        old_time = str(time.time() - 700)  # TTL is 600s
        hash_path.write_text(f"{stored_hash}\n{old_time}")

        # Clean session flag
        _cache_flag(tmp_path, "s1").unlink(missing_ok=True)

        # Second run — TTL expired, should re-inject even though hash matches
        r2 = _run_hook(tmp_path, "Explore", session_id="s2")
        assert r2.returncode == 0
        assert r2.stdout.strip(), "should re-inject after TTL expires"
        _cleanup(tmp_path)

    def test_reinjects_on_content_change(self, tmp_path):
        """When content hash changes (content updated), must re-inject."""
        _make_zf(tmp_path)
        _cleanup(tmp_path)

        # First inject
        r1 = _run_hook(tmp_path, "Explore", session_id="s1")
        assert r1.stdout.strip(), "first inject should emit context"

        # Clean session flag
        _cache_flag(tmp_path, "s1").unlink(missing_ok=True)

        # Change ADR summary content — hash should differ
        decisions = tmp_path / "zie-framework" / "decisions"
        decisions.mkdir(exist_ok=True)
        (decisions / "ADR-000-summary.md").write_text("# Updated ADR Summary\n\nNew content here.")

        # Second run — hash mismatch, should re-inject
        r2 = _run_hook(tmp_path, "Explore", session_id="s2")
        assert r2.returncode == 0
        assert r2.stdout.strip(), "should re-inject when content hash changes"
        _cleanup(tmp_path)

    def test_corrupt_hash_file_triggers_reinject(self, tmp_path):
        """Corrupt hash file (empty or malformed) should trigger re-injection."""
        _make_zf(tmp_path)
        _cleanup(tmp_path)

        # Write a corrupt hash file (single line, no timestamp)
        hash_path = _hash_file(tmp_path)
        hash_path.write_text("badhash")

        r = _run_hook(tmp_path, "Explore", session_id="fresh-session")
        assert r.returncode == 0
        assert r.stdout.strip(), "corrupt hash file should not block injection"
        _cleanup(tmp_path)

    def test_no_hash_file_without_context_files(self, tmp_path):
        """When no ADR summary or project context exists, no hash file should be written."""
        _make_zf(tmp_path, with_context=False)
        _cleanup(tmp_path)

        r = _run_hook(tmp_path, "Explore")
        assert r.returncode == 0
        hash_path = _hash_file(tmp_path)
        # Hash file should NOT be written when content hash is empty string
        # (because _compute_content_hash returns "" when no files exist)
        assert not hash_path.exists(), "no hash file when context files are absent"
        _cleanup(tmp_path)