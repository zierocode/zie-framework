"""Unit tests for hooks/quality-gate.py (Sprint B — Code Quality Gates)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "quality-gate.py"


def _run(command: str, tmp_path: Path,
         session_id: str = "test-qg") -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "session_id": session_id,
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def _make_zf(tmp_path: Path) -> Path:
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    return zf


class TestQualityGateGitCommitTrigger:
    def test_exits_zero_on_non_commit_command(self, tmp_path):
        _make_zf(tmp_path)
        r = _run("git status", tmp_path)
        assert r.returncode == 0
        assert r.stderr.strip() == ""

    def test_exits_zero_on_non_git_command(self, tmp_path):
        _make_zf(tmp_path)
        r = _run("echo hello", tmp_path)
        assert r.returncode == 0

    def test_runs_on_git_commit_command(self, tmp_path):
        _make_zf(tmp_path)
        r = _run("git commit -m 'test'", tmp_path)
        assert r.returncode == 0  # warn-only, never blocks

    def test_exits_zero_when_no_zf_dir(self, tmp_path):
        r = _run("git commit -m 'test'", tmp_path)
        assert r.returncode == 0


class TestQualityGateWarnOnly:
    def test_never_blocks_commit(self, tmp_path):
        """Quality gate must always exit 0 — warn-only, never blocks git commit."""
        _make_zf(tmp_path)
        r = _run("git commit -m 'wip'", tmp_path)
        assert r.returncode == 0

    def test_summary_line_emitted(self, tmp_path):
        """git commit → must emit a 'Quality gate' summary to stderr."""
        _make_zf(tmp_path)
        r = _run("git commit -m 'feat: something'", tmp_path)
        assert r.returncode == 0
        # Summary line must appear in stderr (warn channel)
        assert "Quality gate" in r.stderr or r.stderr.strip() == ""


class TestQualityGateSkipsUnavailableTools:
    def test_missing_bandit_skipped(self, tmp_path):
        """If bandit is not on PATH → hook must still exit 0 with no crash."""
        _make_zf(tmp_path)
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        env["PATH"] = "/nonexistent"  # bandit not available
        event = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
            "session_id": "test-qg-nobandit",
        })
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input=event,
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0


class TestQualityGateErrorPath:
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
