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


class TestConfigTableHardeningKeys:
    def test_subprocess_timeout_s_documented(self):
        content = CLAUDE_MD.read_text()
        assert "subprocess_timeout_s" in content

    def test_safety_agent_timeout_s_documented(self):
        content = CLAUDE_MD.read_text()
        assert "safety_agent_timeout_s" in content

    def test_auto_test_max_wait_s_documented(self):
        content = CLAUDE_MD.read_text()
        assert "auto_test_max_wait_s" in content

    def test_auto_test_timeout_ms_documented(self):
        content = CLAUDE_MD.read_text()
        assert "auto_test_timeout_ms" in content
