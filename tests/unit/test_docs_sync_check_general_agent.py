"""Tests for agentic-pipeline-v2 Task 7: docs-sync uses general-purpose agent."""
from pathlib import Path

RELEASE_PATH = Path(__file__).parents[2] / "commands" / "release.md"
RETRO_PATH = Path(__file__).parents[2] / "commands" / "retro.md"
SKILL_PATH = Path(__file__).parents[2] / "skills" / "docs-sync" / "SKILL.md"


class TestDocsSyncCheckGeneralAgent:
    def test_release_no_docs_sync_check_plugin_agent(self):
        """zie-release must not use zie-framework:docs-sync agent type."""
        text = RELEASE_PATH.read_text()
        assert 'subagent_type="zie-framework:docs-sync"' not in text and \
               "subagent_type='zie-framework:docs-sync'" not in text, \
            "zie-release must not reference zie-framework:docs-sync agent"

    def test_retro_no_docs_sync_check_plugin_agent(self):
        """zie-retro must not use zie-framework:docs-sync agent type."""
        text = RETRO_PATH.read_text()
        assert 'subagent_type="zie-framework:docs-sync"' not in text and \
               "subagent_type='zie-framework:docs-sync'" not in text, \
            "zie-retro must not reference zie-framework:docs-sync agent"

    def test_release_uses_skill_for_docs_sync(self):
        """zie-release uses Skill(zie-framework:docs-sync) for docs sync."""
        text = RELEASE_PATH.read_text()
        assert "docs-sync" in text, \
            "zie-release must reference docs-sync"

    def test_retro_uses_skill_for_docs_sync(self):
        """zie-retro uses Skill(zie-framework:docs-sync) for docs sync."""
        text = RETRO_PATH.read_text()
        assert "Skill(zie-framework:docs-sync)" in text, \
            "zie-retro must use Skill(zie-framework:docs-sync)"

    def test_docs_sync_inline_instructions_in_release(self):
        """zie-release docs-sync references docs-sync skill."""
        text = RELEASE_PATH.read_text()
        assert "docs-sync" in text, \
            "zie-release must reference docs-sync"

    def test_docs_sync_inline_instructions_in_retro(self):
        """zie-retro docs-sync references docs-sync skill."""
        text = RETRO_PATH.read_text()
        assert "docs-sync" in text, \
            "zie-retro must reference docs-sync"


class TestDocsSyncCheckProjectMd:
    def _skill(self):
        return SKILL_PATH.read_text()

    def test_skill_reads_project_md(self):
        """Skill must instruct reading PROJECT.md."""
        assert "PROJECT.md" in self._skill(), \
            "docs-sync SKILL.md must mention PROJECT.md"

    def test_skill_has_step_3b(self):
        """Skill must contain a Step 3b block."""
        assert "3b" in self._skill(), \
            "docs-sync SKILL.md must have a Step 3b"

    def test_skill_strips_slash_prefix(self):
        """Skill must document stripping / prefix from command names."""
        skill = self._skill()
        assert "strip" in skill.lower() or "strip `/`" in skill or "strip the `/`" in skill, \
            "Skill must document stripping / prefix from PROJECT.md command rows"

    def test_skill_excludes_header_rows(self):
        """Skill must document skipping header rows."""
        skill = self._skill()
        assert "header" in skill.lower() or "| Command |" in skill or "| --- |" in skill, \
            "Skill must document skipping table header rows"

    def test_verdict_has_project_md_stale(self):
        """Returned JSON verdict must include project_md_stale field."""
        assert "project_md_stale" in self._skill(), \
            "docs-sync verdict JSON must include project_md_stale"

    def test_verdict_has_missing_and_extra_fields(self):
        """Returned JSON verdict must include missing_from_project_md and extra_in_project_md."""
        skill = self._skill()
        assert "missing_from_project_md" in skill, \
            "Verdict must include missing_from_project_md"
        assert "extra_in_project_md" in skill, \
            "Verdict must include extra_in_project_md"
