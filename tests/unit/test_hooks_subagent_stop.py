"""Tests for hooks/subagent-stop.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "subagent-stop.py")
sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
from utils import project_tmp_path


def run_hook(event: dict, tmp_cwd=None, env_overrides=None):
    env = {**os.environ}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def make_cwd(tmp_path):
    """Return tmp_path with a zie-framework/ subdir present."""
    (tmp_path / "zie-framework").mkdir(parents=True)
    return tmp_path


VALID_EVENT = {
    "agent_id": "abc-123",
    "agent_type": "spec-reviewer",
    "last_assistant_message": "Looks good overall.",
}


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _cleanup_log(tmp_path):
    yield
    log = project_tmp_path("subagent-log", tmp_path.name)
    if log.exists() or log.is_symlink():
        log.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# TestSubagentStopNormalWrite
# ---------------------------------------------------------------------------

class TestSubagentStopNormalWrite:
    def test_log_file_created_on_valid_event(self, tmp_path):
        cwd = make_cwd(tmp_path)
        run_hook(VALID_EVENT, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        assert log.exists(), f"log file not created at {log}"

    def test_log_contains_one_jsonl_line(self, tmp_path):
        cwd = make_cwd(tmp_path)
        run_hook(VALID_EVENT, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        lines = [l for l in log.read_text().splitlines() if l.strip()]
        assert len(lines) == 1

    def test_log_line_is_valid_json(self, tmp_path):
        cwd = make_cwd(tmp_path)
        run_hook(VALID_EVENT, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        line = log.read_text().strip()
        record = json.loads(line)  # must not raise
        assert isinstance(record, dict)

    def test_agent_id_field(self, tmp_path):
        cwd = make_cwd(tmp_path)
        run_hook(VALID_EVENT, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        record = json.loads(log.read_text().strip())
        assert record["agent_id"] == "abc-123"

    def test_agent_type_field(self, tmp_path):
        cwd = make_cwd(tmp_path)
        run_hook(VALID_EVENT, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        record = json.loads(log.read_text().strip())
        assert record["agent_type"] == "spec-reviewer"

    def test_last_message_field(self, tmp_path):
        cwd = make_cwd(tmp_path)
        run_hook(VALID_EVENT, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        record = json.loads(log.read_text().strip())
        assert record["last_message"] == "Looks good overall."

    def test_ts_field_present_and_ends_with_z(self, tmp_path):
        cwd = make_cwd(tmp_path)
        run_hook(VALID_EVENT, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        record = json.loads(log.read_text().strip())
        assert "ts" in record
        assert record["ts"].endswith("Z"), f"ts must end with Z, got: {record['ts']}"

    def test_exits_zero_on_valid_event(self, tmp_path):
        cwd = make_cwd(tmp_path)
        r = run_hook(VALID_EVENT, tmp_cwd=cwd)
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# TestSubagentStopTruncation
# ---------------------------------------------------------------------------

class TestSubagentStopTruncation:
    def test_long_message_truncated_to_500(self, tmp_path):
        cwd = make_cwd(tmp_path)
        event = {**VALID_EVENT, "last_assistant_message": "x" * 1000}
        run_hook(event, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        record = json.loads(log.read_text().strip())
        assert len(record["last_message"]) == 500

    def test_short_message_not_padded(self, tmp_path):
        cwd = make_cwd(tmp_path)
        event = {**VALID_EVENT, "last_assistant_message": "short"}
        run_hook(event, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        record = json.loads(log.read_text().strip())
        assert record["last_message"] == "short"

    def test_exactly_500_message_unchanged(self, tmp_path):
        cwd = make_cwd(tmp_path)
        event = {**VALID_EVENT, "last_assistant_message": "y" * 500}
        run_hook(event, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        record = json.loads(log.read_text().strip())
        assert len(record["last_message"]) == 500


# ---------------------------------------------------------------------------
# TestSubagentStopMissingFields
# ---------------------------------------------------------------------------

class TestSubagentStopMissingFields:
    def test_empty_event_writes_unknown_placeholders(self, tmp_path):
        cwd = make_cwd(tmp_path)
        run_hook({}, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        assert log.exists(), "log must be written even for empty event"
        record = json.loads(log.read_text().strip())
        assert record["agent_id"] == "unknown"
        assert record["agent_type"] == "unknown"
        assert record["last_message"] == ""

    def test_none_last_message_coerced_to_empty_string(self, tmp_path):
        cwd = make_cwd(tmp_path)
        event = {"agent_id": "x", "agent_type": "y", "last_assistant_message": None}
        run_hook(event, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        record = json.loads(log.read_text().strip())
        assert record["last_message"] == ""

    def test_missing_agent_id_defaults_to_unknown(self, tmp_path):
        cwd = make_cwd(tmp_path)
        event = {"agent_type": "plan-reviewer", "last_assistant_message": "ok"}
        run_hook(event, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        record = json.loads(log.read_text().strip())
        assert record["agent_id"] == "unknown"

    def test_exits_zero_on_empty_event(self, tmp_path):
        cwd = make_cwd(tmp_path)
        r = run_hook({}, tmp_cwd=cwd)
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# TestSubagentStopGuardrails
# ---------------------------------------------------------------------------

class TestSubagentStopGuardrails:
    def test_no_write_when_no_zf_dir(self, tmp_path):
        # tmp_path has no zie-framework/ subdir
        r = run_hook(VALID_EVENT, tmp_cwd=tmp_path)
        assert r.returncode == 0
        log = project_tmp_path("subagent-log", tmp_path.name)
        assert not log.exists(), "log must NOT be written on non-zie projects"

    def test_malformed_stdin_exits_zero(self):
        r = subprocess.run(
            [sys.executable, HOOK],
            input="not valid json }{",
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0

    def test_empty_stdin_exits_zero(self):
        r = subprocess.run(
            [sys.executable, HOOK],
            input="",
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# TestSubagentStopSymlinkGuard
# ---------------------------------------------------------------------------

class TestSubagentStopSymlinkGuard:
    def test_symlink_at_log_path_skips_write(self, tmp_path):
        cwd = make_cwd(tmp_path)
        real_target = tmp_path / "sensitive.txt"
        real_target.write_text("do not overwrite")
        log = project_tmp_path("subagent-log", tmp_path.name)
        log.symlink_to(real_target)

        r = run_hook(VALID_EVENT, tmp_cwd=cwd)

        assert r.returncode == 0
        assert real_target.read_text() == "do not overwrite", (
            "symlink target must not be overwritten"
        )

    def test_symlink_guard_prints_warning_to_stderr(self, tmp_path):
        cwd = make_cwd(tmp_path)
        real_target = tmp_path / "sensitive.txt"
        real_target.write_text("safe")
        log = project_tmp_path("subagent-log", tmp_path.name)
        log.symlink_to(real_target)

        r = run_hook(VALID_EVENT, tmp_cwd=cwd)

        assert "subagent" in r.stderr.lower() or "symlink" in r.stderr.lower(), (
            f"expected symlink warning on stderr, got: {r.stderr!r}"
        )


# ---------------------------------------------------------------------------
# TestSubagentStopMultipleEvents
# ---------------------------------------------------------------------------

class TestSubagentStopMultipleEvents:
    def test_three_events_produce_three_lines(self, tmp_path):
        cwd = make_cwd(tmp_path)
        events = [
            {"agent_id": "a1", "agent_type": "spec-reviewer", "last_assistant_message": "msg1"},
            {"agent_id": "a2", "agent_type": "plan-reviewer", "last_assistant_message": "msg2"},
            {"agent_id": "a3", "agent_type": "impl-reviewer", "last_assistant_message": "msg3"},
        ]
        for ev in events:
            run_hook(ev, tmp_cwd=cwd)
        log = project_tmp_path("subagent-log", tmp_path.name)
        lines = [l for l in log.read_text().splitlines() if l.strip()]
        assert len(lines) == 3

    def test_multiple_events_each_line_parseable(self, tmp_path):
        cwd = make_cwd(tmp_path)
        for i in range(3):
            run_hook(
                {"agent_id": f"id-{i}", "agent_type": "reviewer",
                 "last_assistant_message": f"msg{i}"},
                tmp_cwd=cwd,
            )
        log = project_tmp_path("subagent-log", tmp_path.name)
        records = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
        assert [r["agent_id"] for r in records] == ["id-0", "id-1", "id-2"]

    def test_multiple_events_order_preserved(self, tmp_path):
        cwd = make_cwd(tmp_path)
        types = ["spec-reviewer", "plan-reviewer", "impl-reviewer"]
        for t in types:
            run_hook(
                {"agent_id": "x", "agent_type": t, "last_assistant_message": ""},
                tmp_cwd=cwd,
            )
        log = project_tmp_path("subagent-log", tmp_path.name)
        records = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
        assert [r["agent_type"] for r in records] == types
