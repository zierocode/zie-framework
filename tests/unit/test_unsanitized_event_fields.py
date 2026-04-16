"""Tests for Sprint C: unsanitized-event-fields — length caps on event-controlled log values."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
STOPFAILURE = REPO_ROOT / "hooks" / "stopfailure-log.py"
NOTIFICATION = REPO_ROOT / "hooks" / "notification-log.py"
UTILS_EVENT = REPO_ROOT / "hooks" / "utils_event.py"


def _run_stopfailure(tmp_path: Path, event: dict) -> subprocess.CompletedProcess:
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    (zf / "ROADMAP.md").write_text("# ROADMAP\n\n## Now\n\n## Done\n")
    env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
    return subprocess.run(
        [sys.executable, str(STOPFAILURE)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def _run_notification(tmp_path: Path, event: dict) -> subprocess.CompletedProcess:
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
    return subprocess.run(
        [sys.executable, str(NOTIFICATION)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


class TestSanitizeLogFieldLengthCap:
    def test_sanitize_log_field_truncates_long_value(self, tmp_path):
        """sanitize_log_field must truncate values exceeding max_len."""
        sys.path.insert(0, str(REPO_ROOT / "hooks"))
        from utils_event import sanitize_log_field  # noqa: PLC0415

        long_value = "A" * 20_000
        result = sanitize_log_field(long_value, max_len=10240)
        assert len(result) <= 10240, "sanitize_log_field must cap at max_len"

    def test_sanitize_log_field_short_value_unchanged(self, tmp_path):
        """sanitize_log_field must not truncate short values."""
        sys.path.insert(0, str(REPO_ROOT / "hooks"))
        from utils_event import sanitize_log_field  # noqa: PLC0415

        short = "hello world"
        result = sanitize_log_field(short)
        assert result == short

    def test_sanitize_log_field_strips_control_chars(self, tmp_path):
        """sanitize_log_field must still strip control characters (existing behavior)."""
        sys.path.insert(0, str(REPO_ROOT / "hooks"))
        from utils_event import sanitize_log_field  # noqa: PLC0415

        value = "hello\x00\x0a\x1fworld"
        result = sanitize_log_field(value)
        assert "\x00" not in result
        assert "\x0a" not in result
        assert "\x1f" not in result

    def test_sanitize_log_field_default_max_len(self, tmp_path):
        """sanitize_log_field default max_len must cap unbounded input."""
        sys.path.insert(0, str(REPO_ROOT / "hooks"))
        from utils_event import sanitize_log_field  # noqa: PLC0415

        huge = "X" * 100_000
        result = sanitize_log_field(huge)
        assert len(result) <= 10240, "default max_len must be enforced"


class TestStopfailureLogFieldCaps:
    def test_oversized_error_details_capped(self, tmp_path):
        """error_details field larger than limit must not cause crash."""
        big_details = "E" * 50_000
        r = _run_stopfailure(
            tmp_path,
            {
                "error_type": "api_error",
                "error_details": big_details,
            },
        )
        assert r.returncode == 0

    def test_oversized_error_type_capped(self, tmp_path):
        """error_type field larger than limit must not cause crash."""
        big_type = "T" * 50_000
        r = _run_stopfailure(tmp_path, {"error_type": big_type, "error_details": ""})
        assert r.returncode == 0


class TestNotificationLogFieldCaps:
    def test_oversized_message_capped(self, tmp_path):
        """message field larger than limit must not cause crash or disk fill."""
        big_msg = "M" * 50_000
        r = _run_notification(
            tmp_path,
            {
                "notification_type": "permission_prompt",
                "message": big_msg,
            },
        )
        assert r.returncode == 0

    def test_message_cap_prevents_context_injection(self, tmp_path):
        """Oversized message must not appear verbatim in additionalContext output."""
        big_msg = "I" * 50_000
        r = _run_notification(
            tmp_path,
            {
                "notification_type": "permission_prompt",
                "message": big_msg,
            },
        )
        assert r.returncode == 0
        if r.stdout.strip():
            data = json.loads(r.stdout.strip())
            ctx = data.get("additionalContext", "")
            assert len(ctx) < 20_000, "additionalContext must not contain unbounded message"


class TestUnsanitizedFieldsErrorPath:
    @pytest.mark.error_path
    def test_exits_zero_on_malformed_stopfailure_event(self, tmp_path):
        """Malformed JSON to stopfailure-log must exit 0."""
        zf = tmp_path / "zie-framework"
        zf.mkdir(exist_ok=True)
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, str(STOPFAILURE)],
            input="not json {{",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
