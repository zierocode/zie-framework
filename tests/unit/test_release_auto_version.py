"""Tests for agentic-pipeline-v2 Task 3: zie-release auto-accepts version suggestion."""
from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "zie-release.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestReleaseAutoVersion:
    def test_no_confirm_version_prompt(self):
        """'Confirm? (Enter = accept / major / minor / patch to override)' must be removed."""
        text = cmd_text()
        assert "Confirm?" not in text and "Enter = accept" not in text, \
            "zie-release must not show interactive version confirmation prompt"

    def test_version_display_message_present(self):
        """Version is displayed (not prompted) — user can override if wrong."""
        text = cmd_text()
        assert "override" in text.lower() or "Send override" in text or "--bump-to" in text, \
            "zie-release must document override option after auto-accepting version"

    def test_version_suggestion_step_present(self):
        """Version bump calculation still happens."""
        text = cmd_text()
        assert "version bump" in text.lower() or "Suggest version" in text or "bump" in text.lower()

    def test_auto_proceeds_after_version(self):
        """Pipeline continues automatically after version display (no blocking wait)."""
        text = cmd_text()
        # No interactive confirmation gate — just display and continue
        assert "Confirm?" not in text

    def test_bump_version_step_present(self):
        """VERSION file is still written."""
        text = cmd_text()
        assert "Bump VERSION" in text or "bump" in text.lower()
