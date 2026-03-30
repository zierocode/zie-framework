"""Tests for agentic-pipeline-v2 Task 6: zie-implement pre-flight --agent mode warning."""
from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "zie-implement.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestImplementAgentModeWarning:
    def test_agent_mode_check_present(self):
        """zie-implement documents agent mode check."""
        text = cmd_text()
        assert "agent" in text.lower() and ("mode" in text.lower() or "zie-implement-mode" in text), \
            "zie-implement must document agent mode detection"

    def test_warning_message_documented(self):
        """Warning message for non-agent mode is documented."""
        text = cmd_text()
        assert "⚠" in text or "Warning" in text or "warning" in text or \
               "outside agent session" in text or "Recommend" in text, \
            "zie-implement must show warning when not in agent session"

    def test_recommend_agent_mode_command(self):
        """Recommended agent mode command is documented."""
        text = cmd_text()
        assert "zie-implement-mode" in text, \
            "zie-implement must reference zie-framework:zie-implement-mode"

    def test_continue_option_available(self):
        """User can choose to continue or cancel."""
        text = cmd_text()
        assert "continue" in text.lower() or "yes" in text.lower(), \
            "zie-implement must allow user to continue outside agent mode"

    def test_normal_flow_unchanged(self):
        """Normal implementation flow is unchanged."""
        text = cmd_text()
        assert "RED" in text and "GREEN" in text and "REFACTOR" in text, \
            "TDD flow must remain unchanged"
