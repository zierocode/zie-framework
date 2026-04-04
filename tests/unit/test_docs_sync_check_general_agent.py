"""Tests for agentic-pipeline-v2 Task 7: docs-sync-check uses general-purpose agent."""
from pathlib import Path

RELEASE_PATH = Path(__file__).parents[2] / "commands" / "release.md"
RETRO_PATH = Path(__file__).parents[2] / "commands" / "retro.md"


class TestDocsSyncCheckGeneralAgent:
    def test_release_no_docs_sync_check_plugin_agent(self):
        """zie-release must not use zie-framework:docs-sync-check agent type."""
        text = RELEASE_PATH.read_text()
        assert 'subagent_type="zie-framework:docs-sync-check"' not in text and \
               "subagent_type='zie-framework:docs-sync-check'" not in text, \
            "zie-release must not reference zie-framework:docs-sync-check agent"

    def test_retro_no_docs_sync_check_plugin_agent(self):
        """zie-retro must not use zie-framework:docs-sync-check agent type."""
        text = RETRO_PATH.read_text()
        assert 'subagent_type="zie-framework:docs-sync-check"' not in text and \
               "subagent_type='zie-framework:docs-sync-check'" not in text, \
            "zie-retro must not reference zie-framework:docs-sync-check agent"

    def test_release_uses_skill_for_docs_sync(self):
        """zie-release uses Skill(zie-framework:docs-sync-check) for docs sync."""
        text = RELEASE_PATH.read_text()
        assert "docs-sync-check" in text, \
            "zie-release must reference docs-sync-check"

    def test_retro_uses_skill_for_docs_sync(self):
        """zie-retro uses Skill(zie-framework:docs-sync-check) for docs sync."""
        text = RETRO_PATH.read_text()
        assert "Skill(zie-framework:docs-sync-check)" in text, \
            "zie-retro must use Skill(zie-framework:docs-sync-check)"

    def test_docs_sync_inline_instructions_in_release(self):
        """zie-release docs-sync references docs-sync-check skill."""
        text = RELEASE_PATH.read_text()
        assert "docs-sync-check" in text, \
            "zie-release must reference docs-sync-check"

    def test_docs_sync_inline_instructions_in_retro(self):
        """zie-retro docs-sync references docs-sync-check skill."""
        text = RETRO_PATH.read_text()
        assert "docs-sync-check" in text, \
            "zie-retro must reference docs-sync-check"
