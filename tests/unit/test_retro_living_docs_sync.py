from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


class TestRetroLivingDocsSync:
    def _retro_text(self) -> str:
        return (COMMANDS_DIR / "zie-retro.md").read_text()

    def test_claude_md_sync_step_present(self):
        assert "CLAUDE.md" in self._retro_text(), \
            "zie-retro.md must contain a CLAUDE.md sync step"

    def test_readme_md_sync_step_present(self):
        assert "README.md" in self._retro_text(), \
            "zie-retro.md must contain a README.md sync step"

    def test_in_sync_fallback_present(self):
        assert "in sync" in self._retro_text(), \
            "zie-retro.md must include an 'in sync' fallback message"

    def test_change_logging_instruction_present(self):
        text = self._retro_text()
        assert "Updated CLAUDE.md" in text, \
            "zie-retro.md must include 'Updated CLAUDE.md' change-logging instruction"
