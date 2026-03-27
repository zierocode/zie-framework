"""Tests for datetime.utcnow() deprecation fix in subagent-stop.py."""
from pathlib import Path


def test_no_utcnow_in_subagent_stop():
    """subagent-stop.py must not use deprecated datetime.utcnow()."""
    source = Path("hooks/subagent-stop.py").read_text()
    assert "utcnow" not in source, "datetime.utcnow() is deprecated — use datetime.now(timezone.utc)"


def test_timezone_import_present():
    """subagent-stop.py must import timezone for datetime.now(timezone.utc)."""
    source = Path("hooks/subagent-stop.py").read_text()
    assert "timezone" in source
