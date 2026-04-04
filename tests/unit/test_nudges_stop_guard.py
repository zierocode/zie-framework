"""Tests for proactive nudge checks added to stop-guard.py."""
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "stop-guard.py")


def run_hook(event: dict, cwd: str, env_overrides: dict = None):
    env = {**os.environ, "CLAUDE_CWD": cwd, "CLAUDE_SESSION_ID": str(uuid.uuid4())}
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


class TestCoverageNudge:
    def test_nudge_when_coverage_missing(self, tmp_path):
        """Prints coverage nudge when .coverage file is absent."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_something.py").write_text("def test_x(): pass\n")
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n\n## Done\n")
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        assert "[zie-framework] nudge:" in r.stdout
        assert "coverage" in r.stdout.lower()

    def test_no_coverage_nudge_when_coverage_fresh(self, tmp_path):
        """No coverage nudge when .coverage is newer than all test files."""
        import time
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_something.py"
        test_file.write_text("def test_x(): pass\n")
        time.sleep(0.02)
        cov_file = tmp_path / ".coverage"
        cov_file.write_text("coverage data")
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n\n## Done\n")
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        assert "coverage data is stale" not in r.stdout

    def test_no_coverage_nudge_when_no_tests_dir(self, tmp_path):
        """No nudge when tests/ directory does not exist."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n\n## Done\n")
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        assert "coverage data is stale" not in r.stdout


class TestStaleBacklogNudge:
    def test_nudge_when_next_item_older_than_30_days(self, tmp_path):
        """Prints stale backlog nudge when a Next item date is > 30 days ago."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / "ROADMAP.md").write_text(
            "## Now\n\n"
            "## Next\n"
            "- [ ] old-item — [backlog](backlog/old-item.md) 2020-01-01\n\n"
            "## Done\n"
        )
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        assert "[zie-framework] nudge:" in r.stdout
        assert "30 days" in r.stdout

    def test_no_stale_nudge_when_next_items_recent(self, tmp_path):
        """No stale backlog nudge when all Next items are within 30 days."""
        import datetime
        recent = (datetime.date.today() - datetime.timedelta(days=5)).isoformat()
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / "ROADMAP.md").write_text(
            f"## Now\n\n"
            f"## Next\n"
            f"- [ ] recent-item — {recent}\n\n"
            "## Done\n"
        )
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        assert "30 days" not in r.stdout

    def test_no_stale_nudge_when_no_roadmap(self, tmp_path):
        """No nudge when zie-framework/ROADMAP.md is missing."""
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        assert "30 days" not in r.stdout

    def test_nudge_prefix_format(self, tmp_path):
        """Nudge output starts with '[zie-framework] nudge:' prefix."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / "ROADMAP.md").write_text(
            "## Now\n\n"
            "## Next\n"
            "- [ ] stale — 2020-06-01\n\n"
            "## Done\n"
        )
        r = run_hook({}, cwd=str(tmp_path))
        assert "[zie-framework] nudge:" in r.stdout

    def test_all_three_nudges_independent(self, tmp_path):
        """Coverage + stale backlog nudges fire independently as separate lines."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_x.py").write_text("def test_x(): pass\n")
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / "ROADMAP.md").write_text(
            "## Now\n\n"
            "## Next\n"
            "- [ ] old — 2019-01-01\n\n"
            "## Done\n"
        )
        r = run_hook({}, cwd=str(tmp_path))
        nudge_lines = [ln for ln in r.stdout.splitlines() if "[zie-framework] nudge:" in ln]
        assert len(nudge_lines) >= 2

    def test_stop_hook_active_skips_all_nudges(self, tmp_path):
        """stop_hook_active guard skips nudge checks entirely."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / "ROADMAP.md").write_text(
            "## Now\n\n## Next\n- [ ] stale — 2019-01-01\n\n## Done\n"
        )
        r = run_hook({"stop_hook_active": True}, cwd=str(tmp_path))
        assert r.returncode == 0
        assert "[zie-framework] nudge:" not in r.stdout


class TestNudgeTTLGate:
    def test_nudge_skipped_on_cache_hit(self, tmp_path):
        """When nudge-check sentinel is fresh, nudges do not run."""
        import sys as _sys
        _sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
        from utils_roadmap import write_git_status_cache
        session_id = str(uuid.uuid4())
        write_git_status_cache(session_id, "nudge-check", "1")
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / "ROADMAP.md").write_text(
            "## Now\n\n"
            "## Next\n"
            "- [ ] old-item — 2019-01-01\n\n"
            "## Done\n"
        )
        r = run_hook({}, cwd=str(tmp_path), env_overrides={"CLAUDE_SESSION_ID": session_id})
        assert r.returncode == 0
        assert "[zie-framework] nudge:" not in r.stdout

    def test_nudge_runs_on_cache_miss(self, tmp_path):
        """When nudge-check sentinel is absent, nudges run normally."""
        session_id = str(uuid.uuid4())
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / "ROADMAP.md").write_text(
            "## Now\n\n"
            "## Next\n"
            "- [ ] old-item — 2019-01-01\n\n"
            "## Done\n"
        )
        r = run_hook({}, cwd=str(tmp_path), env_overrides={"CLAUDE_SESSION_ID": session_id})
        assert r.returncode == 0
        assert "[zie-framework] nudge:" in r.stdout
        assert "30 days" in r.stdout

    def test_nudge_runs_when_no_session_id(self, tmp_path):
        """When CLAUDE_SESSION_ID is unset, nudges run (degenerate: no caching)."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / "ROADMAP.md").write_text(
            "## Now\n\n"
            "## Next\n"
            "- [ ] old-item — 2019-01-01\n\n"
            "## Done\n"
        )
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_SESSION_ID"}
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps({}),
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
        assert "[zie-framework] nudge:" in r.stdout
