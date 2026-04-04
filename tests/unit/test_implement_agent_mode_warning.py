"""Tests for agentic-pipeline-v2 Task 6: zie-implement pre-flight --agent mode warning."""
from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "implement.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestImplementAgentModeWarning:
    def test_agent_mode_check_present(self):
        """zie-implement documents agent mode check."""
        text = cmd_text()
        assert "agent" in text.lower() and ("mode" in text.lower() or "zie-implement-mode" in text), \
            "zie-implement must document agent mode detection"

    def test_advisory_message_documented(self):
        """Advisory message for non-agent mode is documented (non-blocking)."""
        text = cmd_text()
        assert "Tip" in text or "advisory" in text.lower() or "zie-implement-mode" in text, \
            "zie-implement must show advisory (non-blocking) when not in agent session"

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

    def test_no_blocking_yes_no_prompt(self):
        """Agent mode check must NOT block with yes/no — it is advisory only."""
        text = cmd_text()
        # The old blocking pattern: "if no → STOP. If yes → continue"
        assert 'if no → STOP' not in text and 'Continue anyway? (yes / no)' not in text, \
            "implement.md agent mode check must be advisory (non-blocking), not a yes/no gate"

    def test_advisory_is_non_blocking(self):
        """Step 0 must continue immediately without waiting for user input."""
        text = cmd_text()
        assert "advisory" in text.lower() or "continue immediately" in text.lower() or \
               "do not block" in text.lower(), \
            "Step 0 must explicitly state it is advisory and non-blocking"

    def test_normal_flow_unchanged(self):
        """Normal implementation flow is unchanged."""
        text = cmd_text()
        assert "RED" in text and "GREEN" in text and "REFACTOR" in text, \
            "TDD flow must remain unchanged"
