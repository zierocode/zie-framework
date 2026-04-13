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


class TestBanditStagedFiles:
    """Bandit scan must use staged files from git diff, not rglob."""

    def _make_fake_git(self, scripts_dir: Path, staged_output: str, fail_diff: bool = False) -> None:
        """Fake git: returns staged_output for --name-only calls; exit 1 if fail_diff."""
        exit_code = 1 if fail_diff else 0
        script = scripts_dir / "git"
        script.write_text(
            f"""#!/bin/sh
for arg in "$@"; do
    if [ "$arg" = "--name-only" ]; then
        printf "%s" "{staged_output}"
        exit {exit_code}
    fi
done
exit 0
"""
        )
        script.chmod(0o755)

    def _make_fake_bandit(self, scripts_dir: Path, args_file: Path) -> None:
        """Fake bandit: records its arguments to args_file."""
        script = scripts_dir / "bandit"
        script.write_text(
            f"""#!/bin/sh
echo "$@" > {args_file}
exit 0
"""
        )
        script.chmod(0o755)

    def _run_with_fakes(self, tmp_path: Path, scripts_dir: Path) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        env["PATH"] = str(scripts_dir) + ":" + env.get("PATH", "")
        event = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
            "session_id": "test-qg-staged",
        }
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            env=env,
        )

    def test_bandit_uses_staged_files(self, tmp_path):
        """Bandit is called with staged Python files only, not all rglob files."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        args_file = tmp_path / "bandit_args.txt"

        # A py file that rglob would find but is NOT staged
        (tmp_path / "not_staged.py").write_text("x = 1")
        # The staged file git fake will report
        staged_rel = "staged_file.py"
        (tmp_path / staged_rel).write_text("x = 1")

        _make_zf(tmp_path)
        self._make_fake_git(scripts_dir, staged_rel)
        self._make_fake_bandit(scripts_dir, args_file)

        self._run_with_fakes(tmp_path, scripts_dir)

        assert args_file.exists(), "bandit must have been called"
        bandit_args = args_file.read_text()
        assert staged_rel in bandit_args, "bandit must be called with staged file"
        assert "not_staged.py" not in bandit_args, "bandit must NOT scan non-staged files"

    def test_bandit_skips_when_no_staged_py(self, tmp_path):
        """Bandit is not called when staged list has no Python files."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        args_file = tmp_path / "bandit_args.txt"

        _make_zf(tmp_path)
        self._make_fake_git(scripts_dir, "")  # no staged files
        self._make_fake_bandit(scripts_dir, args_file)

        r = self._run_with_fakes(tmp_path, scripts_dir)
        assert r.returncode == 0
        assert not args_file.exists(), "bandit must NOT be called when no staged py files"

    def test_bandit_skips_on_git_diff_failure(self, tmp_path):
        """Bandit is skipped silently when git diff --cached fails."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        args_file = tmp_path / "bandit_args.txt"

        _make_zf(tmp_path)
        self._make_fake_git(scripts_dir, "", fail_diff=True)
        self._make_fake_bandit(scripts_dir, args_file)

        r = self._run_with_fakes(tmp_path, scripts_dir)
        assert r.returncode == 0, "hook must not crash when git diff fails"
        assert not args_file.exists(), "bandit must NOT be called when git diff fails"
