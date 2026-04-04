"""Tests for agentic-pipeline-v2 Tasks 4+5: zie-retro uses general-purpose agent + auto-commit."""
from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "zie-retro.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestRetroGeneralPurposeAgent:
    def test_no_retro_format_plugin_agent(self):
        """zie-retro must not use zie-framework:retro-format agent type."""
        text = cmd_text()
        assert 'subagent_type="zie-framework:retro-format"' not in text and \
               "subagent_type='zie-framework:retro-format'" not in text, \
            "zie-retro must not reference zie-framework:retro-format agent"

    def test_no_general_purpose_agent(self):
        """zie-retro must not spawn general-purpose agents — ADRs are written inline."""
        text = cmd_text()
        assert 'subagent_type="general-purpose"' not in text and \
               "subagent_type='general-purpose'" not in text, \
            "zie-retro must not spawn general-purpose agents for ADR/ROADMAP writes"

    def test_inline_adr_instructions(self):
        """Agent instructions cover ADR 5-section format."""
        text = cmd_text()
        assert "ADR" in text and ("Status" in text or "Context" in text or "Decision" in text), \
            "zie-retro agent must have inline ADR format instructions"



class TestRetroAutoCommit:
    def test_auto_commit_present(self):
        """zie-retro auto-commits ADRs + components.md."""
        text = cmd_text()
        assert "git commit" in text or "auto-commit" in text.lower() or \
               "git add" in text, \
            "zie-retro must auto-commit retro outputs"

    def test_commit_message_format(self):
        """Commit message format: chore: retro vX.Y.Z."""
        text = cmd_text()
        assert "chore: retro" in text or "retro v" in text, \
            "zie-retro commit message must use 'chore: retro' prefix"

    def test_push_on_failure_non_blocking(self):
        """Git push failure is non-blocking."""
        text = cmd_text()
        assert "push failed" in text.lower() or "non-blocking" in text.lower() or \
               "Manual push" in text or "manual push" in text.lower() or \
               "skip" in text.lower(), \
            "zie-retro must handle git push failure gracefully"
