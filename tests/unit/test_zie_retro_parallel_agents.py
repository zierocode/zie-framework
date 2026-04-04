"""Tests for zie-retro.md inline ADR+ROADMAP writes."""
from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "retro.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestRetroInlineWrites:
    def test_adr_and_roadmap_both_present(self):
        """Both ADR-write and ROADMAP-update instructions are in the retro command."""
        text = cmd_text()
        assert "ADR" in text and "ROADMAP" in text, \
            "zie-retro must have both ADR and ROADMAP update instructions"

    def test_no_run_in_background_in_retro(self):
        """Retro must not use run_in_background (inline writes, not agents)."""
        text = cmd_text()
        assert "run_in_background" not in text, \
            "zie-retro must not use run_in_background for ADR/ROADMAP writes"

    def test_no_skill_references_in_prompts(self):
        """ADR/ROADMAP section must not spawn zie-framework:retro-format agents."""
        text = cmd_text()
        assert 'subagent_type="zie-framework:retro-format"' not in text and \
               "subagent_type='zie-framework:retro-format'" not in text, \
            "Retro must not reference zie-framework:retro-format agent"

    def test_no_subagent_type_in_adr_section(self):
        """ADR/ROADMAP write section must not spawn any agents."""
        text = cmd_text()
        assert 'subagent_type=' not in text, \
            "zie-retro must not use subagent_type in ADR/ROADMAP section"
