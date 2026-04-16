"""Tests for init-scaffold-claude-code-config: template existence and .ignore merge logic."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES = REPO_ROOT / "templates"
INIT_MD = REPO_ROOT / "commands" / "init.md"


class TestTemplatesExist:
    """Verify all three new template files exist and are valid."""

    def test_claude_settings_template_exists(self):
        path = TEMPLATES / "claude-settings.json.template"
        assert path.is_file(), "templates/claude-settings.json.template must exist"

    def test_claude_settings_template_is_valid_json(self):
        path = TEMPLATES / "claude-settings.json.template"
        data = json.loads(path.read_text())
        assert "permissions" in data
        assert "allow" in data["permissions"]
        assert isinstance(data["permissions"]["allow"], list)
        assert len(data["permissions"]["allow"]) > 0

    def test_claude_rules_sdlc_template_exists(self):
        path = TEMPLATES / "claude-rules-sdlc.md.template"
        assert path.is_file(), "templates/claude-rules-sdlc.md.template must exist"

    def test_claude_rules_sdlc_template_is_markdown(self):
        path = TEMPLATES / "claude-rules-sdlc.md.template"
        content = path.read_text()
        assert content.startswith("#"), "SDLC rules template must start with a heading"

    def test_dot_ignore_template_exists(self):
        path = TEMPLATES / "dot-ignore.template"
        assert path.is_file(), "templates/dot-ignore.template must exist"

    def test_dot_ignore_template_has_patterns(self):
        path = TEMPLATES / "dot-ignore.template"
        lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
        assert len(lines) >= 5, f".ignore template should have >= 5 patterns, got {len(lines)}"
        assert "__pycache__/" in lines
        assert "node_modules/" in lines
        assert ".env" in lines


class TestInitMdReferences:
    """Verify commands/init.md references the new templates."""

    def test_init_md_references_claude_settings(self):
        content = INIT_MD.read_text()
        assert "claude-settings.json.template" in content, (
            "init.md must reference templates/claude-settings.json.template"
        )

    def test_init_md_references_claude_rules(self):
        content = INIT_MD.read_text()
        assert "claude-rules-sdlc.md.template" in content, (
            "init.md must reference templates/claude-rules-sdlc.md.template"
        )

    def test_init_md_references_dot_ignore(self):
        content = INIT_MD.read_text()
        assert "dot-ignore.template" in content, "init.md must reference templates/dot-ignore.template"

    def test_init_md_has_step_12(self):
        content = INIT_MD.read_text()
        assert "Scaffold `.claude/` configuration" in content, (
            "init.md must have step 12 for .claude/ config scaffolding"
        )


class TestDotIgnoreMerge:
    """Test .ignore merge logic: append missing patterns without duplicates."""

    def _get_template_patterns(self) -> list[str]:
        path = TEMPLATES / "dot-ignore.template"
        return [line.strip() for line in path.read_text().splitlines() if line.strip()]

    def test_merge_appends_missing_patterns(self, tmp_path: Path):
        """If .ignore has some patterns, merge adds only the missing ones."""
        existing = tmp_path / ".ignore"
        existing.write_text("__pycache__/\n.env\n")
        template_patterns = self._get_template_patterns()
        existing_lines = set(existing.read_text().splitlines())

        new_lines = [p for p in template_patterns if p not in existing_lines]
        merged = existing.read_text().rstrip("\n") + "\n" + "\n".join(new_lines) + "\n"
        existing.write_text(merged)

        result_lines = [line for line in existing.read_text().splitlines() if line.strip()]
        for pattern in template_patterns:
            assert pattern in result_lines, f"Pattern '{pattern}' missing after merge"

    def test_merge_no_duplicates(self, tmp_path: Path):
        """Merge does not create duplicate lines."""
        existing = tmp_path / ".ignore"
        existing.write_text("__pycache__/\n.env\n")
        template_patterns = self._get_template_patterns()
        existing_lines = set(existing.read_text().splitlines())

        new_lines = [p for p in template_patterns if p not in existing_lines]
        merged = existing.read_text().rstrip("\n") + "\n" + "\n".join(new_lines) + "\n"
        existing.write_text(merged)

        result_lines = [line for line in existing.read_text().splitlines() if line.strip()]
        assert len(result_lines) == len(set(result_lines)), "No duplicate lines in merged .ignore"

    def test_merge_preserves_existing(self, tmp_path: Path):
        """Merge preserves existing patterns that aren't in the template."""
        existing = tmp_path / ".ignore"
        custom_line = "*.log"
        existing.write_text(f"__pycache__/\n{custom_line}\n")
        template_patterns = self._get_template_patterns()
        existing_lines = set(existing.read_text().splitlines())

        new_lines = [p for p in template_patterns if p not in existing_lines]
        merged = existing.read_text().rstrip("\n") + "\n" + "\n".join(new_lines) + "\n"
        existing.write_text(merged)

        assert custom_line in existing.read_text()
