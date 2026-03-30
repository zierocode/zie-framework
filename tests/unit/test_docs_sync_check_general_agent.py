"""Tests for agentic-pipeline-v2 Task 7: docs-sync-check uses general-purpose agent."""
from pathlib import Path

RELEASE_PATH = Path(__file__).parents[2] / "commands" / "zie-release.md"
RETRO_PATH = Path(__file__).parents[2] / "commands" / "zie-retro.md"


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

    def test_release_uses_general_purpose_for_docs_sync(self):
        """zie-release uses general-purpose agent for docs sync."""
        text = RELEASE_PATH.read_text()
        assert "general-purpose" in text, \
            "zie-release must use general-purpose agent"

    def test_retro_uses_general_purpose_for_docs_sync(self):
        """zie-retro uses general-purpose agent for docs sync."""
        text = RETRO_PATH.read_text()
        assert "general-purpose" in text, \
            "zie-retro must use general-purpose agent"

    def test_docs_sync_inline_instructions_in_release(self):
        """zie-release agent has inline sync check instructions."""
        text = RELEASE_PATH.read_text()
        assert "CLAUDE.md" in text and "README.md" in text, \
            "zie-release docs-sync agent must reference CLAUDE.md and README.md"

    def test_docs_sync_inline_instructions_in_retro(self):
        """zie-retro agent has inline sync check instructions."""
        text = RETRO_PATH.read_text()
        assert "CLAUDE.md" in text and "README.md" in text, \
            "zie-retro docs-sync agent must reference CLAUDE.md and README.md"
