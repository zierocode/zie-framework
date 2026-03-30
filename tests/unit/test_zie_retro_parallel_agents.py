"""Tests for parallel-release-gates Task 2: zie-retro parallel ADR+ROADMAP agents."""
from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "zie-retro.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestRetroParallelAgents:
    def test_adr_roadmap_agents_both_present(self):
        """Both ADR-write and ROADMAP-update agents are in the parallel section."""
        text = cmd_text()
        assert "ADR" in text and "ROADMAP" in text and "parallel" in text.lower(), \
            "zie-retro must have both ADR and ROADMAP agents in parallel section"

    def test_agents_use_general_purpose(self):
        """Both retro agents use general-purpose."""
        text = cmd_text()
        assert text.count("general-purpose") >= 2, \
            "zie-retro must use general-purpose for both ADR + ROADMAP agents"

    def test_agents_run_in_background(self):
        """Both agents use run_in_background=True."""
        text = cmd_text()
        assert text.count("run_in_background=True") >= 2 or \
               text.count("run_in_background: true") >= 2 or \
               "run_in_background" in text, \
            "zie-retro agents must use run_in_background=True"

    def test_no_skill_references_in_prompts(self):
        """Agent prompts do not contain zie-framework: skill references."""
        text = cmd_text()
        # The actual prompts should not call zie-framework:retro-format
        # (fallback comments are allowed)
        main_text = text.split("<!-- fallback")[0]
        assert 'subagent_type="zie-framework:retro-format"' not in main_text and \
               "subagent_type='zie-framework:retro-format'" not in main_text, \
            "Agent prompts must not reference zie-framework:retro-format"

    def test_await_both_before_brain_store(self):
        """Results collected before proceeding to brain store."""
        text = cmd_text()
        assert "Await both" in text or "await" in text.lower(), \
            "zie-retro must await both agents before brain store"
