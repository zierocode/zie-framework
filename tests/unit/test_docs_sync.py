"""Doc-state assertions for docs-sync-and-completeness pass."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent


class TestMakefileBumpCallsSyncVersion:
    def test_bump_target_calls_bump_extra(self):
        """bump target must call _bump-extra (project-specific version file hook)."""
        content = (REPO_ROOT / "Makefile").read_text()
        import re
        match = re.search(r'^bump:.*?(?=^\w+:|\Z)', content, re.MULTILINE | re.DOTALL)
        assert match, "bump target not found in Makefile"
        bump_block = match.group(0)
        assert "_bump-extra" in bump_block, (
            "bump target does not call _bump-extra"
        )


class TestProjectMd:
    def _content(self):
        return (REPO_ROOT / "zie-framework" / "PROJECT.md").read_text()

    def test_version_is_current(self):
        """PROJECT.md must show the current VERSION."""
        version = (REPO_ROOT / "VERSION").read_text().strip()
        assert f"**Version**: {version}" in self._content(), (
            f"PROJECT.md version is not {version} — run: make sync-version"
        )

    def test_commands_table_has_sprint(self):
        assert "/sprint" in self._content(), "PROJECT.md Commands table missing /sprint"

    def test_commands_table_has_chore(self):
        assert "/chore" in self._content(), "PROJECT.md Commands table missing /chore"

    def test_commands_table_has_hotfix(self):
        assert "/hotfix" in self._content(), "PROJECT.md Commands table missing /hotfix"

    def test_commands_table_has_spike(self):
        assert "/spike" in self._content(), "PROJECT.md Commands table missing /spike"

    def test_skills_table_no_retro_format_ghost(self):
        assert "retro-format" not in self._content(), (
            "PROJECT.md Skills table has ghost entry 'retro-format' — skill was deleted"
        )

    def test_skills_table_has_load_context(self):
        assert "load-context" in self._content(), (
            "PROJECT.md Skills table missing load-context"
        )

    def test_skills_table_has_reviewer_context(self):
        assert "reviewer-context" in self._content(), (
            "PROJECT.md Skills table missing reviewer-context"
        )

    def test_commands_table_header_is_english(self):
        """Commands table header must use 'Description', not Thai."""
        content = self._content()
        assert "ทำอะไร" not in content, (
            "PROJECT.md still contains Thai header 'ทำอะไร'"
        )
        assert "| Command | Description |" in content, (
            "Commands table header 'Description' not found"
        )


class TestArchitectureMd:
    def _content(self):
        return (REPO_ROOT / "zie-framework" / "project" / "architecture.md").read_text()

    def test_v1_5_0_entry_exists(self):
        assert "**v1.5.0**" in self._content(), "v1.5.0 entry missing from architecture.md"

    def test_v1_6_0_entry_exists(self):
        assert "**v1.6.0**" in self._content(), "v1.6.0 entry missing from architecture.md"

    def test_v1_7_0_entry_exists(self):
        assert "**v1.7.0**" in self._content(), "v1.7.0 entry missing from architecture.md"

    def test_v1_8_0_entry_exists(self):
        assert "**v1.8.0**" in self._content(), "v1.8.0 entry missing from architecture.md"

    def test_v1_5_0_mentions_knowledge_hash(self):
        """v1.5.0 entry must reference knowledge-hash.py extraction."""
        assert "knowledge-hash.py" in self._content(), (
            "v1.5.0 entry should mention knowledge-hash.py"
        )


class TestComponentsMd:
    def _content(self):
        return (REPO_ROOT / "zie-framework" / "project" / "components.md").read_text()

    def test_knowledge_hash_entry_exists(self):
        assert "knowledge-hash.py" in self._content(), (
            "knowledge-hash.py not documented in components.md"
        )

    def test_knowledge_hash_not_in_hooks_section(self):
        """knowledge-hash.py must be in a utility section, not listed as a hook."""
        content = self._content()
        in_hooks = False
        for line in content.splitlines():
            if "## Hooks" in line:
                in_hooks = True
            elif in_hooks and line.startswith("## "):
                break
            if in_hooks and "knowledge-hash.py" in line:
                raise AssertionError(
                    "knowledge-hash.py is listed inside the Hooks section — "
                    "it should be in a Utility Scripts section"
                )

    def test_utility_scripts_section_exists(self):
        assert "Utility Scripts" in self._content(), (
            "No 'Utility Scripts' section found in components.md"
        )


class TestClaudeMd:
    def _content(self):
        return (REPO_ROOT / "CLAUDE.md").read_text()

    def test_sdlc_commands_has_chore(self):
        assert "/chore" in self._content(), "CLAUDE.md SDLC Commands table missing /chore"

    def test_sdlc_commands_has_hotfix(self):
        assert "/hotfix" in self._content(), "CLAUDE.md SDLC Commands table missing /hotfix"

    def test_sdlc_commands_has_spike(self):
        assert "/spike" in self._content(), "CLAUDE.md SDLC Commands table missing /spike"

    def test_optional_deps_documents_playwright(self):
        assert "playwright" in self._content(), (
            "CLAUDE.md must document playwright optional dependency"
        )

    def test_optional_deps_documents_zie_memory(self):
        content = self._content()
        assert "zie-memory" in content or "zie_memory" in content, (
            "CLAUDE.md must document zie-memory optional dependency"
        )

    def test_sync_version_in_dev_commands(self):
        assert "sync-version" in self._content(), (
            "CLAUDE.md Development Commands missing 'make sync-version'"
        )


class TestReadmeMd:
    def _content(self):
        return (REPO_ROOT / "README.md").read_text()

    def test_skills_section_exists(self):
        assert "## Skills" in self._content(), (
            "README.md missing ## Skills section"
        )

    def test_skills_table_has_tdd_loop(self):
        assert "tdd-loop" in self._content(), (
            "Skills table missing tdd-loop entry"
        )

    def test_skills_table_has_zie_audit(self):
        assert "zie-audit" in self._content(), (
            "Skills table missing zie-audit entry"
        )

    def test_skills_section_mentions_subagents(self):
        content = self._content()
        assert "subagent" in content.lower() or "automatically" in content.lower(), (
            "Skills section should explain skills are invoked automatically"
        )
