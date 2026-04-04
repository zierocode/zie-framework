from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


class TestRetroLivingDocsSync:
    def _retro_text(self) -> str:
        return (COMMANDS_DIR / "zie-retro.md").read_text()

    def test_docs_sync_check_skill_invoked(self):
        assert "docs-sync-check" in self._retro_text(), \
            "zie-retro.md must invoke docs-sync-check skill for docs sync"

    def test_docs_sync_check_skill_call_present(self):
        assert "Skill(zie-framework:docs-sync-check)" in self._retro_text(), \
            "zie-retro.md must use Skill(zie-framework:docs-sync-check)"

    def test_docs_sync_verdict_printed(self):
        text = self._retro_text()
        assert "verdict" in text.lower() or "details" in text.lower() or \
               "docs-sync" in text.lower(), \
            "zie-retro.md must print docs-sync check result"

    def test_docs_sync_skip_guard_present(self):
        text = self._retro_text()
        assert "release:" in text or "skipped" in text.lower(), \
            "zie-retro.md must have docs-sync skip guard for release commits"
