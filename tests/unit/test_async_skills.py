"""Test async skills background execution patterns."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD_DIR = REPO_ROOT / "commands"


class TestAsyncSkillPatterns:
    """Test that long-running Skills are converted to Agent + background."""

    def test_zie_retro_uses_agent_background(self):
        """zie-retro.md must use Agent + run_in_background for retro and docs-sync.
        Uses general-purpose agent (not plugin-specific) per agentic-pipeline-v2."""
        text = (CMD_DIR / "zie-retro.md").read_text()
        # Must use general-purpose agent (plugin-specific agents require plugin reload)
        assert 'subagent_type="general-purpose"' in text or \
               "general-purpose" in text, \
            "zie-retro.md must use general-purpose agent (agentic-pipeline-v2)"
        assert 'run_in_background' in text, \
            "zie-retro.md must use run_in_background=true"
        assert "TaskCreate" in text, \
            "zie-retro.md must use TaskCreate for progress tracking"

    def test_zie_release_uses_agent_background(self):
        """zie-release.md must use Agent + run_in_background for docs-sync-check.
        Uses general-purpose agent (not plugin-specific) per agentic-pipeline-v2."""
        text = (CMD_DIR / "zie-release.md").read_text()
        # Must use general-purpose agent (plugin-specific agents require plugin reload)
        assert 'subagent_type="general-purpose"' in text or \
               "general-purpose" in text, \
            "zie-release.md must use general-purpose agent (agentic-pipeline-v2)"
        assert 'run_in_background' in text, \
            "zie-release.md must use run_in_background=true"
        assert "TaskCreate" in text, \
            "zie-release.md must use TaskCreate for progress tracking"

    def test_zie_implement_uses_taskcreate_for_verify(self):
        """zie-implement.md must use TaskCreate for verify step."""
        text = (CMD_DIR / "zie-implement.md").read_text()
        assert "TaskCreate" in text, \
            "zie-implement.md must use TaskCreate for verify step"
        assert "verify" in text.lower(), \
            "zie-implement.md must reference verify"
        # Skill call should still be present (not converted to Agent)
        assert 'Skill(zie-framework:verify)' in text, \
            "zie-implement.md must still call Skill(zie-framework:verify) inline"

    def test_fallback_comments_present(self):
        """Fallback comments must be present for graceful degradation."""
        retro = (CMD_DIR / "zie-retro.md").read_text()
        assert "<!-- fallback:" in retro and "Skill(zie-framework:retro-format)" in retro, \
            "zie-retro.md must have fallback comment for retro-format"

        release = (CMD_DIR / "zie-release.md").read_text()
        assert "<!-- fallback:" in release and "docs-sync-check" in release, \
            "zie-release.md must have fallback comment referencing docs-sync-check"
