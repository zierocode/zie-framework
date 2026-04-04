"""Test async skills background execution patterns."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD_DIR = REPO_ROOT / "commands"


class TestAsyncSkillPatterns:
    """Test that long-running Skills are converted to Agent + background."""

    def test_zie_retro_uses_agent_for_file_writing(self):
        """zie-retro.md must use Agent + run_in_background for file-writing (ADRs, ROADMAP).
        Text-processing steps are inlined; only file-writing uses background agents."""
        text = (CMD_DIR / "zie-retro.md").read_text()
        assert 'subagent_type="general-purpose"' in text or "general-purpose" in text, \
            "zie-retro.md must use general-purpose agent for ADR/ROADMAP writing"
        assert 'run_in_background' in text, \
            "zie-retro.md must use run_in_background=True for file-writing agents"
        assert "Write ADRs" in text or "Write ADR" in text, \
            "zie-retro.md must have ADR-writing agent"

    def test_zie_release_uses_background_execution(self):
        """zie-release.md must use inline Bash with run_in_background for parallel gates."""
        text = (CMD_DIR / "zie-release.md").read_text()
        assert 'run_in_background' in text, \
            "zie-release.md must use run_in_background=True for parallel gates"
        assert 'make test-int' in text, \
            "zie-release.md must invoke make test-int for Gate 2"
        assert "Agent(" not in text, \
            "zie-release.md must use inline Bash, not Agent() spawning"

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

    def test_fallback_handling_present(self):
        """Graceful degradation must be documented."""
        retro = (CMD_DIR / "zie-retro.md").read_text()
        # Retro uses inline reasoning — no Agent() fallback needed for text-processing
        # File-writing agents still have fallback documented
        assert "Failure mode" in retro or "fallback" in retro.lower() or "skip" in retro, \
            "zie-retro.md must document failure/skip behavior"

        release = (CMD_DIR / "zie-release.md").read_text()
        assert "docs-sync-check unavailable" in release, \
            "zie-release.md must document docs-sync-check unavailable skip message"
