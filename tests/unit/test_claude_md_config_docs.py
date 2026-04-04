"""Verify hook config keys are documented in config-reference.md (canonical location)."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CONFIG_REF = REPO_ROOT / "zie-framework" / "project" / "config-reference.md"


def test_safety_check_mode_documented():
    content = CONFIG_REF.read_text()
    assert "safety_check_mode" in content, "config-reference.md must document safety_check_mode config key"


def test_safety_check_mode_values_documented():
    content = CONFIG_REF.read_text()
    assert '"regex"' in content or "'regex'" in content, "config-reference.md must document regex mode"
    assert '"agent"' in content or "'agent'" in content, "config-reference.md must document agent mode"


class TestConfigTableHardeningKeys:
    def test_subprocess_timeout_s_documented(self):
        content = CONFIG_REF.read_text()
        assert "subprocess_timeout_s" in content

    def test_safety_agent_timeout_s_documented(self):
        content = CONFIG_REF.read_text()
        assert "safety_agent_timeout_s" in content

    def test_auto_test_max_wait_s_documented(self):
        content = CONFIG_REF.read_text()
        assert "auto_test_max_wait_s" in content

    def test_auto_test_timeout_ms_documented(self):
        content = CONFIG_REF.read_text()
        assert "auto_test_timeout_ms" in content
