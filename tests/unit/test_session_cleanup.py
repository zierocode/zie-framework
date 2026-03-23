"""Tests for hooks/session-cleanup.py"""
import json
import os
import sys
import subprocess
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
from utils import project_tmp_path


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
    def test_deletes_project_scoped_tmp_files(self, tmp_path):
        project = tmp_path.name
        tmp1 = project_tmp_path("last-test", project)
        tmp2 = project_tmp_path("edit-count", project)
        tmp1.write_text("x")
        tmp2.write_text("1")
        assert tmp1.exists()
        assert tmp2.exists()

        r = run_hook(project)
        assert r.returncode == 0
        assert not tmp1.exists(), f"{tmp1} should have been deleted"
        assert not tmp2.exists(), f"{tmp2} should have been deleted"

    def test_does_not_delete_other_project_files(self, tmp_path):
        our_project = tmp_path.name
        other_project = "other-" + tmp_path.name
        other_file = project_tmp_path("last-test", other_project)
        other_file.write_text("keep me")

        r = run_hook(our_project)
        assert r.returncode == 0
        assert other_file.exists(), "File from other project must not be deleted"
        other_file.unlink(missing_ok=True)

    def test_exits_cleanly_when_no_matching_files(self, tmp_path):
        r = run_hook(tmp_path.name + "-nonexistent-xyz")
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


class TestSessionCleanupTmpPathScoped:
    def test_no_hardcoded_project_names_in_test_source(self):
        """Tests must not use hardcoded project names — use tmp_path.name instead."""
        src = Path(__file__).read_text()
        hardcoded = ["zie-cleanup-test-" + "proj", "zie-cleanup-" + "ours", "zie-cleanup-" + "other"]
        for name in hardcoded:
            assert name not in src, (
                f"Hardcoded project name {name!r} found in test source — "
                "use tmp_path.name to derive unique project names"
            )


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
