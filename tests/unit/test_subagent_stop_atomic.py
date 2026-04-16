"""Tests verifying atomic append behavior in hooks/subagent-stop.py."""

import json
import os
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "hooks"))

from utils_io import project_tmp_path  # noqa: E402


def _run_subagent_stop(tmp_path, agent_id="agent-1", agent_type="reviewer"):
    """Run subagent-stop.py with injected project root."""
    import subprocess

    hook = REPO_ROOT / "hooks" / "subagent-stop.py"
    event = {"agent_id": agent_id, "agent_type": agent_type, "last_assistant_message": "done"}
    env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
    return subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def _make_cwd(tmp_path):
    """Create a minimal zie-framework project root."""
    (tmp_path / "zie-framework").mkdir(parents=True, exist_ok=True)
    return tmp_path


class TestSubagentStopAtomicWrite:
    def _cleanup_log(self, cwd):
        import shutil

        log = project_tmp_path("subagent-log", cwd.name)
        if log.is_dir():
            shutil.rmtree(log, ignore_errors=True)
        else:
            log.unlink(missing_ok=True)
        lock = Path(str(log) + ".lock")
        lock.unlink(missing_ok=True)

    def test_first_write_creates_file(self, tmp_path):
        """Absent log file is created with the first entry."""
        cwd = _make_cwd(tmp_path)
        self._cleanup_log(cwd)
        result = _run_subagent_stop(cwd)
        assert result.returncode == 0
        log = project_tmp_path("subagent-log", cwd.name)
        assert log.exists()
        lines = [ln for ln in log.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["agent_id"] == "agent-1"

    def test_second_write_appends(self, tmp_path):
        """Second invocation appends; two lines present in correct order."""
        cwd = _make_cwd(tmp_path)
        self._cleanup_log(cwd)
        _run_subagent_stop(cwd, agent_id="first")
        _run_subagent_stop(cwd, agent_id="second")
        log = project_tmp_path("subagent-log", cwd.name)
        lines = [ln for ln in log.read_text().splitlines() if ln.strip()]
        assert len(lines) == 2
        assert json.loads(lines[0])["agent_id"] == "first"
        assert json.loads(lines[1])["agent_id"] == "second"

    def test_concurrent_writes_both_present(self, tmp_path):
        """Two threads write simultaneously; both lines are present."""
        cwd = _make_cwd(tmp_path)
        self._cleanup_log(cwd)
        errors = []

        def write(agent_id):
            try:
                _run_subagent_stop(cwd, agent_id=agent_id)
            except Exception as e:
                errors.append(str(e))

        t1 = threading.Thread(target=write, args=("thread-a",))
        t2 = threading.Thread(target=write, args=("thread-b",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert not errors
        log = project_tmp_path("subagent-log", cwd.name)
        lines = [ln for ln in log.read_text().splitlines() if ln.strip()]
        assert len(lines) == 2
        ids = {json.loads(ln)["agent_id"] for ln in lines}
        assert ids == {"thread-a", "thread-b"}

    def test_atomic_write_error_exits_zero(self, tmp_path):
        """atomic_write raising OSError does not cause non-zero exit."""
        cwd = _make_cwd(tmp_path)
        self._cleanup_log(cwd)
        hook = REPO_ROOT / "hooks" / "subagent-stop.py"
        # Make it a directory so writes fail
        log = project_tmp_path("subagent-log", cwd.name)
        log.mkdir(parents=True, exist_ok=True)

        event = {"agent_id": "x", "agent_type": "spec-review", "last_assistant_message": ""}
        env = {**os.environ, "CLAUDE_CWD": str(cwd)}
        import subprocess

        result = subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0
