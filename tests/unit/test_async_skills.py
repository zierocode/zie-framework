"""Test async skills background execution patterns."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD_DIR = REPO_ROOT / "commands"


class TestAsyncSkillPatterns:
    """Test that long-running Skills are converted to Agent + background."""

    def test_zie_retro_writes_adrs_inline(self):
        """zie-retro.md must write ADRs inline (no agents, no run_in_background)."""
        text = (CMD_DIR / "retro.md").read_text()
        assert "Write" in text and "ADR" in text, \
            "zie-retro.md must have inline Write for ADR files"
        assert 'run_in_background' not in text, \
            "zie-retro.md must NOT use run_in_background for ADR/ROADMAP writes"
        assert "Agent(" not in text, \
            "zie-retro.md ADR/ROADMAP section must not spawn agents"

    def test_zie_release_uses_background_execution(self):
        """zie-release.md must use inline Bash with run_in_background for parallel gates."""
        text = (CMD_DIR / "release.md").read_text()
        assert 'run_in_background' in text, \
            "zie-release.md must use run_in_background=True for parallel gates"
        assert 'make test-int' in text, \
            "zie-release.md must invoke make test-int for Gate 2"
        assert "Agent(" not in text, \
            "zie-release.md must use inline Bash, not Agent() spawning"

    def test_zie_implement_uses_taskcreate_for_verify(self):
        """zie-implement.md must use TaskCreate for verify step."""
        text = (CMD_DIR / "implement.md").read_text()
        assert "TaskCreate" in text, \
            "zie-implement.md must use TaskCreate for verify step"
        assert "verify" in text.lower(), \
            "zie-implement.md must reference verify"
        # Skill call should still be present (not converted to Agent)
        assert 'Skill(zie-framework:verify)' in text, \
            "zie-implement.md must still call Skill(zie-framework:verify) inline"

    def test_fallback_handling_present(self):
        """Graceful degradation must be documented."""
        retro = (CMD_DIR / "retro.md").read_text()
        assert "fail" in retro.lower() or "error" in retro.lower() or "continue" in retro.lower(), \
            "zie-retro.md must document error/failure/continue handling"

        release = (CMD_DIR / "release.md").read_text()
        assert "docs-sync-check unavailable" in release, \
            "zie-release.md must document docs-sync-check unavailable skip message"
