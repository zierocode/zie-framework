"""Tests for hooks/stopfailure-log.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "stopfailure-log.py")

SAMPLE_ROADMAP = """## Now
- [ ] Implement login flow
- [ ] Add JWT validation
- [ ] Write integration tests

## Next
- [ ] Add refresh tokens
"""


def run_hook(tmp_cwd, event=None, env_overrides=None):
    if event is None:
        event = {"error_type": "api_error"}
    env = {**os.environ, "CLAUDE_CWD": str(tmp_cwd)}
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def make_cwd(tmp_path, roadmap=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if roadmap:
        (zf / "ROADMAP.md").write_text(roadmap)
    return tmp_path


def failure_log_path(cwd):
    """Mirror the hook's log path calculation."""
    import re
    safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd.name)
    return Path(f"/tmp/zie-{safe}-failure-log")


class TestLogWritten:
    def test_log_written_rate_limit(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        run_hook(cwd, event={"error_type": "rate_limit"})
        assert log.exists(), "failure-log must be created for rate_limit"
        content = log.read_text()
        assert "error_type=rate_limit" in content

    def test_log_written_billing_error(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        run_hook(cwd, event={"error_type": "billing_error"})
        assert log.exists(), "failure-log must be created for billing_error"
        assert "error_type=billing_error" in log.read_text()

    def test_log_written_api_error_silent(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        r = run_hook(cwd, event={"error_type": "api_error"})
        assert log.exists(), "failure-log must be created for api_error"
        assert "error_type=api_error" in log.read_text()
        assert r.stderr.strip() == "", "api_error must produce no stderr notification"

    def test_log_written_overloaded_error_silent(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        r = run_hook(cwd, event={"error_type": "overloaded_error"})
        assert log.exists()
        assert "error_type=overloaded_error" in log.read_text()
        assert r.stderr.strip() == "", "overloaded_error must produce no stderr notification"

    def test_log_written_unknown_error_silent(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        r = run_hook(cwd, event={"error_type": "some_new_error_type"})
        assert log.exists()
        assert "error_type=some_new_error_type" in log.read_text()
        assert r.stderr.strip() == ""


class TestNotification:
    def test_rate_limit_stderr_notification(self, tmp_path):
        cwd = make_cwd(tmp_path)
        r = run_hook(cwd, event={"error_type": "rate_limit"})
        assert "rate_limit" in r.stderr
        assert "Wait before resuming" in r.stderr

    def test_billing_error_stderr_notification(self, tmp_path):
        cwd = make_cwd(tmp_path)
        r = run_hook(cwd, event={"error_type": "billing_error"})
        assert "billing_error" in r.stderr
        assert "Wait before resuming" in r.stderr


class TestWipInLogEntry:
    def test_wip_in_log_entry(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        run_hook(cwd, event={"error_type": "api_error"})
        content = log.read_text()
        assert "login flow" in content or "wip=" in content, (
            "log entry must include Now-lane WIP context"
        )

    def test_wip_empty_when_no_roadmap(self, tmp_path):
        cwd = make_cwd(tmp_path)  # no ROADMAP.md
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        run_hook(cwd, event={"error_type": "api_error"})
        content = log.read_text()
        assert "wip=" in content


class TestGuardrails:
    def test_no_zie_framework_dir_exits_clean(self, tmp_path):
        # tmp_path has no zie-framework/ subdir
        log = failure_log_path(tmp_path)
        log.unlink(missing_ok=True)
        r = run_hook(tmp_path, event={"error_type": "rate_limit"})
        assert r.returncode == 0
        assert not log.exists(), "no log must be written when zie-framework/ absent"

    def test_malformed_stdin_exits_clean(self, tmp_path):
        log = failure_log_path(tmp_path)
        log.unlink(missing_ok=True)
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, HOOK],
            input="not valid json{{{",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
        assert not log.exists(), "no log must be written on malformed stdin"

    def test_log_appends_on_multiple_calls(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        run_hook(cwd, event={"error_type": "api_error"})
        run_hook(cwd, event={"error_type": "rate_limit"})
        lines = [ln for ln in log.read_text().splitlines() if ln.strip()]
        assert len(lines) == 2, f"expected 2 log lines, got {len(lines)}"

    def test_no_crash_on_tmp_write_failure(self, tmp_path):
        """Hook must exit 0 even when the log path is unwritable."""
        import shutil
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        # Clean up any prior state (file or directory)
        if log.is_dir():
            shutil.rmtree(log)
        else:
            log.unlink(missing_ok=True)
        # Make the log path a directory so open(..., "a") raises IsADirectoryError
        log.mkdir(parents=True, exist_ok=True)
        try:
            r = run_hook(cwd, event={"error_type": "api_error"})
            assert r.returncode == 0, "hook must not crash on write failure"
        finally:
            shutil.rmtree(log, ignore_errors=True)


class TestHooksJsonRegistration:
    def test_stopfailure_registered_in_hooks_json(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        import json as _json
        data = _json.loads(hooks_json.read_text())
        hooks_block = data.get("hooks", {})
        assert "StopFailure" in hooks_block, (
            "hooks/hooks.json must register a StopFailure event block"
        )

    def test_stopfailure_command_references_correct_script(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        import json as _json
        data = _json.loads(hooks_json.read_text())
        entries = data["hooks"]["StopFailure"]
        commands = [
            h["command"]
            for entry in entries
            for h in entry.get("hooks", [])
            if h.get("type") == "command"
        ]
        assert any("stopfailure-log.py" in cmd for cmd in commands), (
            "StopFailure hook must reference stopfailure-log.py"
        )
