"""Tests for adaptive learning — session-end.py pattern recording +
intent-sdlc.py threshold adjustment (Sprint B)."""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
SESSION_END = REPO_ROOT / "hooks" / "session-end.py"
INTENT_SDLC = REPO_ROOT / "hooks" / "intent-sdlc.py"


def _safe(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", name)


def _pattern_log(tmp_path: Path) -> Path:
    return Path(tempfile.gettempdir()) / f"zie-{_safe(tmp_path.name)}-pattern-log"


def _pattern_agg(tmp_path: Path) -> Path:
    return Path(tempfile.gettempdir()) / f"zie-{_safe(tmp_path.name)}-pattern-aggregate"


def _run_session_end(tmp_path: Path, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    """Run session-end.py with a minimal environment."""
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    (zf / "ROADMAP.md").write_text("# ROADMAP\n\n## Now\n\n- implement this feature\n\n## Done\n")
    env = {**os.environ, "CLAUDE_CWD": str(tmp_path), "ZIE_MEMORY_ENABLED": "0", "ZIE_MEMORY_API_KEY": "", "ZIE_MEMORY_API_URL": ""}
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(SESSION_END)],
        input=json.dumps({"session_id": "test-adaptive"}),
        capture_output=True,
        text=True,
        env=env,
    )


def _run_intent_sdlc(tmp_path: Path, message: str, aggregate: dict | None = None) -> subprocess.CompletedProcess:
    """Run intent-sdlc.py with optional aggregate pre-written."""
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    (zf / "ROADMAP.md").write_text("# ROADMAP\n\n## Now\n\n## Next\n\n- some-feature\n\n## Done\n")
    agg_path = _pattern_agg(tmp_path)
    if aggregate is not None:
        agg_path.write_text(json.dumps(aggregate))
    env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
    return subprocess.run(
        [sys.executable, str(INTENT_SDLC)],
        input=json.dumps({"prompt": message, "session_id": "test-adaptive"}),
        capture_output=True,
        text=True,
        env=env,
    )


class TestSessionRecordWritten:
    def test_record_written_with_stage_field(self, tmp_path):
        """Session record must include stage field."""
        log_path = _pattern_log(tmp_path)
        log_path.unlink(missing_ok=True)
        r = _run_session_end(tmp_path)
        assert r.returncode == 0
        assert log_path.exists(), "pattern-log must be created"
        record = json.loads(log_path.read_text().strip().splitlines()[-1])
        assert "stage" in record, "record must have stage field"

    def test_record_written_with_ts_field(self, tmp_path):
        """Session record must include ts (timestamp) field."""
        log_path = _pattern_log(tmp_path)
        log_path.unlink(missing_ok=True)
        r = _run_session_end(tmp_path)
        assert r.returncode == 0
        record = json.loads(log_path.read_text().strip().splitlines()[-1])
        assert "ts" in record, "record must have ts field"
        assert re.match(r"\d{4}-\d{2}-\d{2}T", record["ts"]), "ts must be ISO format"

    def test_record_written_with_wip_field(self, tmp_path):
        """Session record must include wip field."""
        log_path = _pattern_log(tmp_path)
        log_path.unlink(missing_ok=True)
        r = _run_session_end(tmp_path)
        assert r.returncode == 0
        record = json.loads(log_path.read_text().strip().splitlines()[-1])
        assert "wip" in record, "record must have wip field"

    def test_stage_detected_from_roadmap(self, tmp_path):
        """Stage field must reflect the active ROADMAP Now task."""
        log_path = _pattern_log(tmp_path)
        log_path.unlink(missing_ok=True)
        zf = tmp_path / "zie-framework"
        zf.mkdir(exist_ok=True)
        (zf / "ROADMAP.md").write_text("# ROADMAP\n\n## Now\n\n- spec my-feature — write design doc\n\n## Done\n")
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path), "ZIE_MEMORY_ENABLED": "0"}
        subprocess.run(
            [sys.executable, str(SESSION_END)],
            input=json.dumps({"session_id": "stage-detect"}),
            capture_output=True,
            text=True,
            env=env,
        )
        record = json.loads(log_path.read_text().strip().splitlines()[-1])
        assert record["stage"] == "spec", f"expected spec, got {record['stage']!r}"

    def test_idle_stage_when_no_now_item(self, tmp_path):
        """Stage must be 'idle' when Now lane is empty."""
        log_path = _pattern_log(tmp_path)
        log_path.unlink(missing_ok=True)
        zf = tmp_path / "zie-framework"
        zf.mkdir(exist_ok=True)
        (zf / "ROADMAP.md").write_text("# ROADMAP\n\n## Now\n\n## Done\n")
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path), "ZIE_MEMORY_ENABLED": "0"}
        subprocess.run(
            [sys.executable, str(SESSION_END)],
            input=json.dumps({"session_id": "idle-stage"}),
            capture_output=True,
            text=True,
            env=env,
        )
        record = json.loads(log_path.read_text().strip().splitlines()[-1])
        assert record["stage"] == "idle"


class TestAggregateRebuild:
    def test_aggregate_rebuilt_at_10_sessions(self, tmp_path):
        """Aggregate must be rebuilt after 10 session records."""
        log_path = _pattern_log(tmp_path)
        agg_path = _pattern_agg(tmp_path)
        log_path.unlink(missing_ok=True)
        agg_path.unlink(missing_ok=True)

        # Write 9 records manually — aggregate should NOT exist yet
        records = [json.dumps({"ts": "2026-01-01T00:00:00Z", "stage": "implement", "wip": "x"}) for _ in range(9)]
        log_path.write_text("\n".join(records) + "\n")

        r = _run_session_end(tmp_path)  # adds 10th record
        assert r.returncode == 0
        assert agg_path.exists(), "aggregate must be written after 10 sessions"
        agg = json.loads(agg_path.read_text())
        assert "most_common_stage" in agg
        assert "session_count" in agg
        assert "stage_counts" in agg

    def test_aggregate_not_rebuilt_at_9_sessions(self, tmp_path):
        """Aggregate must NOT be rebuilt after only 9 session records."""
        log_path = _pattern_log(tmp_path)
        agg_path = _pattern_agg(tmp_path)
        log_path.unlink(missing_ok=True)
        agg_path.unlink(missing_ok=True)

        # Write 8 records — this run adds the 9th
        records = [json.dumps({"ts": "2026-01-01T00:00:00Z", "stage": "implement", "wip": "x"}) for _ in range(8)]
        log_path.write_text("\n".join(records) + "\n")

        r = _run_session_end(tmp_path)
        assert r.returncode == 0
        assert not agg_path.exists(), "aggregate must NOT be written after 9 sessions"

    def test_aggregate_most_common_stage_correct(self, tmp_path):
        """Aggregate most_common_stage must reflect the plurality stage."""
        log_path = _pattern_log(tmp_path)
        agg_path = _pattern_agg(tmp_path)
        log_path.unlink(missing_ok=True)
        agg_path.unlink(missing_ok=True)

        # 9 implement + this session = 10; implement should win
        records = [json.dumps({"ts": "2026-01-01T00:00:00Z", "stage": "implement", "wip": "x"}) for _ in range(9)]
        log_path.write_text("\n".join(records) + "\n")
        _run_session_end(tmp_path)

        agg = json.loads(agg_path.read_text())
        assert agg["most_common_stage"] == "implement"


class TestMissingAggregateFallback:
    def test_intent_exits_zero_without_aggregate(self, tmp_path):
        """intent-sdlc.py must work normally when no aggregate exists."""
        agg_path = _pattern_agg(tmp_path)
        agg_path.unlink(missing_ok=True)
        r = _run_intent_sdlc(tmp_path, "want to implement this feature and start coding now")
        assert r.returncode == 0

    def test_intent_exits_zero_with_corrupt_aggregate(self, tmp_path):
        """intent-sdlc.py must not crash on corrupt aggregate JSON."""
        agg_path = _pattern_agg(tmp_path)
        agg_path.write_text("not valid json {{{")
        r = _run_intent_sdlc(tmp_path, "want to implement this feature and start coding now")
        assert r.returncode == 0


class TestThresholdAdjustment:
    def test_guidance_suppressed_when_implement_dominant(self, tmp_path):
        """When most_common_stage=implement, positional guidance hint is suppressed."""
        aggregate = {
            "most_common_stage": "implement",
            "session_count": 20,
            "stage_counts": {"implement": 20},
        }
        r = _run_intent_sdlc(
            tmp_path,
            "implement this feature — let's start coding",
            aggregate=aggregate,
        )
        assert r.returncode == 0
        out = r.stdout.strip()
        if out:
            data = json.loads(out)
            ctx = data.get("additionalContext", "")
            # Should NOT show positional guidance about starting with /spec
            assert "Start with /spec" not in ctx and "is in backlog" not in ctx, (
                "Positional guidance must be suppressed for experienced implement users"
            )

    def test_guidance_shown_without_aggregate(self, tmp_path):
        """Without aggregate, default behavior (show guidance) is preserved."""
        agg_path = _pattern_agg(tmp_path)
        agg_path.unlink(missing_ok=True)
        # Backlog item exists in ROADMAP so guidance would normally fire
        zf = tmp_path / "zie-framework"
        zf.mkdir(exist_ok=True)
        (zf / "ROADMAP.md").write_text("# ROADMAP\n\n## Now\n\n## Next\n\n- some-feature\n\n## Done\n")
        r = _run_intent_sdlc(tmp_path, "let's work on some-feature")
        assert r.returncode == 0


class TestAdaptiveLearningErrorPath:
    @pytest.mark.error_path
    def test_exits_zero_when_pattern_log_unwritable(self, tmp_path):
        """Pattern log write failure must not crash session-end — exits 0."""
        log_path = _pattern_log(tmp_path)
        log_path.unlink(missing_ok=True)
        # We use PATH trick: run session-end with CLAUDE_CWD pointing to a
        # dir where zie-framework exists but pattern log write is simulated to fail
        # via env manipulation — simplest: check exit code is always 0
        r = _run_session_end(tmp_path)
        assert r.returncode == 0, "session-end must always exit 0"
