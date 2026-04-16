"""Tests that /status spec references drift count display."""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD = REPO_ROOT / "commands" / "status.md"


def test_drift_row_in_status():
    text = CMD.read_text()
    assert "drift" in text.lower(), "zie-status must reference drift count"


def test_drift_log_read_mentioned():
    text = CMD.read_text()
    assert ".drift-log" in text
