"""Tests for hooks/session-cleanup.py"""
import json
import os
import sys
import subprocess
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run_hook(cwd_name, stdin_data=None):
    hook = os.path.join(REPO_ROOT, "hooks", "session-cleanup.py")
    env = os.environ.copy()
    # Build a fake CLAUDE_CWD that ends with cwd_name
    env["CLAUDE_CWD"] = f"/fake/path/{cwd_name}"
    if stdin_data is None:
        stdin_data = json.dumps({"stop_reason": "end_turn"})
    return subprocess.run(
        [sys.executable, hook],
        input=stdin_data,
        capture_output=True,
        text=True,
        env=env,
    )


class TestSessionCleanupDeletes:
    def test_deletes_project_scoped_tmp_files(self):
        project = "zie-cleanup-test-proj"
        tmp1 = Path(f"/tmp/zie-{project}-last-test")
        tmp2 = Path(f"/tmp/zie-{project}-edit-count")
        tmp1.write_text("x")
        tmp2.write_text("1")
        assert tmp1.exists()
        assert tmp2.exists()

        r = run_hook(project)
        assert r.returncode == 0
        assert not tmp1.exists(), f"{tmp1} should have been deleted"
        assert not tmp2.exists(), f"{tmp2} should have been deleted"

    def test_does_not_delete_other_project_files(self):
        our_project = "zie-cleanup-ours"
        other_project = "zie-cleanup-other"
        other_file = Path(f"/tmp/zie-{other_project}-last-test")
        other_file.write_text("keep me")

        r = run_hook(our_project)
        assert r.returncode == 0
        assert other_file.exists(), "File from other project must not be deleted"
        # cleanup
        other_file.unlink(missing_ok=True)

    def test_exits_cleanly_when_no_matching_files(self):
        r = run_hook("zie-cleanup-nonexistent-proj-xyz")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_cleanup_uses_same_rule_as_utils(self):
        """Glob pattern used by session-cleanup must match safe_project_name() output."""
        sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
        from utils import safe_project_name
        project = "my project!"
        safe = safe_project_name(project)
        tmp1 = Path(f"/tmp/zie-{safe}-last-test")
        tmp1.write_text("x")
        r = run_hook(project)
        assert r.returncode == 0
        assert not tmp1.exists(), f"{tmp1} should have been deleted"


class TestSessionCleanupGuards:
    def test_malformed_stdin_exits_zero(self):
        hook = os.path.join(REPO_ROOT, "hooks", "session-cleanup.py")
        r = subprocess.run(
            [sys.executable, hook],
            input="not json at all",
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0

    def test_empty_stdin_exits_zero(self):
        hook = os.path.join(REPO_ROOT, "hooks", "session-cleanup.py")
        r = subprocess.run(
            [sys.executable, hook],
            input="",
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
