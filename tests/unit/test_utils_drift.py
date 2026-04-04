"""Tests for hooks/utils_drift.py — drift log helpers."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
from utils_drift import append_drift_event, close_drift_track, read_drift_count


def _zf(tmp_path):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True, exist_ok=True)
    return tmp_path


class TestAppendDriftEvent:
    def test_creates_drift_log(self, tmp_path):
        cwd = _zf(tmp_path)
        append_drift_event(cwd, {"track": "hotfix", "slug": "abc"})
        log = tmp_path / "zie-framework" / ".drift-log"
        assert log.exists()

    def test_appends_ndjson_line(self, tmp_path):
        cwd = _zf(tmp_path)
        append_drift_event(cwd, {"track": "hotfix", "slug": "abc"})
        lines = (tmp_path / "zie-framework" / ".drift-log").read_text().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["track"] == "hotfix"
        assert parsed["slug"] == "abc"

    def test_multiple_appends(self, tmp_path):
        cwd = _zf(tmp_path)
        for i in range(3):
            append_drift_event(cwd, {"track": "chore", "slug": f"task-{i}"})
        lines = (tmp_path / "zie-framework" / ".drift-log").read_text().splitlines()
        assert len(lines) == 3

    def test_rolling_trim_at_200(self, tmp_path):
        cwd = _zf(tmp_path)
        for i in range(205):
            append_drift_event(cwd, {"track": "chore", "slug": f"t-{i}"})
        lines = (tmp_path / "zie-framework" / ".drift-log").read_text().splitlines()
        assert len(lines) == 200

    def test_keeps_last_200_events(self, tmp_path):
        cwd = _zf(tmp_path)
        for i in range(205):
            append_drift_event(cwd, {"track": "chore", "slug": f"t-{i}"})
        lines = (tmp_path / "zie-framework" / ".drift-log").read_text().splitlines()
        last = json.loads(lines[-1])
        assert last["slug"] == "t-204"

    def test_no_crash_on_unwritable_parent(self, tmp_path):
        append_drift_event(tmp_path / "nonexistent", {"track": "spike", "slug": "x"})


class TestReadDriftCount:
    def test_missing_file_returns_zero(self, tmp_path):
        assert read_drift_count(tmp_path / "zie-framework") == 0

    def test_counts_lines(self, tmp_path):
        cwd = _zf(tmp_path)
        for i in range(5):
            append_drift_event(cwd, {"track": "chore", "slug": f"c-{i}"})
        assert read_drift_count(cwd) == 5

    def test_empty_file_returns_zero(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".drift-log").write_text("")
        assert read_drift_count(tmp_path) == 0


class TestCloseDriftTrack:
    def test_closes_matching_open_event(self, tmp_path):
        cwd = _zf(tmp_path)
        append_drift_event(cwd, {"track": "hotfix", "slug": "my-fix", "closed_at": None})
        close_drift_track(cwd, "my-fix")
        log = tmp_path / "zie-framework" / ".drift-log"
        events = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
        closed = [e for e in events if e["slug"] == "my-fix"]
        assert len(closed) == 1
        assert closed[-1]["closed_at"] is not None

    def test_no_crash_on_missing_log(self, tmp_path):
        close_drift_track(tmp_path, "nonexistent")
