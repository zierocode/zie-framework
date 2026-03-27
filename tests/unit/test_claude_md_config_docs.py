"""Verify CLAUDE.md documents the safety_check_mode config key."""
from pathlib import Path

CLAUDE_MD = Path(__file__).parents[2] / "CLAUDE.md"


def test_safety_check_mode_documented():
    content = CLAUDE_MD.read_text()
    assert "safety_check_mode" in content, "CLAUDE.md must document safety_check_mode config key"


def test_safety_check_mode_values_documented():
    content = CLAUDE_MD.read_text()
    assert '"regex"' in content or "'regex'" in content, "CLAUDE.md must document regex mode"
    assert '"agent"' in content or "'agent'" in content, "CLAUDE.md must document agent mode"
