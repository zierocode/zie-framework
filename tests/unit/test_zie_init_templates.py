"""
Tests for /zie-init: CLAUDE.md template + zie-memory seeding
Acceptance criteria from: zie-framework/specs/zie-init-claude-md-memory.md
"""
import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def read(rel_path: str) -> str:
    with open(os.path.join(REPO_ROOT, rel_path)) as f:
        return f.read()


# ── AC1: CLAUDE.md template exists with all required placeholders ────────────

class TestClaudeMdTemplate:
    TEMPLATE_PATH = "templates/CLAUDE.md.template"
    REQUIRED_PLACEHOLDERS = [
        "{{project_name}}",
        "{{project_description}}",
        "{{tech_stack}}",
        "{{test_runner}}",
        "{{build_commands}}",
    ]

    def test_template_file_exists(self):
        path = os.path.join(REPO_ROOT, self.TEMPLATE_PATH)
        assert os.path.isfile(path), f"Missing: {self.TEMPLATE_PATH}"

    def test_template_has_all_placeholders(self):
        content = read(self.TEMPLATE_PATH)
        for placeholder in self.REQUIRED_PLACEHOLDERS:
            assert placeholder in content, (
                f"Placeholder '{placeholder}' missing from {self.TEMPLATE_PATH}"
            )


# ── AC2: zie-init.md contains a CLAUDE.md step that skips if file exists ─────

class TestZieInitClaudeMdStep:
    COMMAND_PATH = "commands/zie-init.md"

    def test_command_has_claude_md_step(self):
        content = read(self.COMMAND_PATH)
        assert "CLAUDE.md" in content, "zie-init.md must contain a CLAUDE.md step"

    def test_claude_md_step_is_idempotent(self):
        content = read(self.COMMAND_PATH)
        # Must mention skipping if the file already exists
        assert re.search(r"CLAUDE\.md.*skip|skip.*CLAUDE\.md", content, re.IGNORECASE | re.DOTALL), (
            "zie-init.md must skip CLAUDE.md creation if file already exists"
        )


# ── AC3: zie-memory step stores structured context ────────────────────────────

class TestZieInitMemoryStep:
    COMMAND_PATH = "commands/zie-init.md"

    def test_memory_step_stores_project_type(self):
        content = read(self.COMMAND_PATH)
        assert "project_type" in content or "Type:" in content, (
            "zie-memory step must store project type"
        )

    def test_memory_step_stores_test_runner(self):
        content = read(self.COMMAND_PATH)
        assert "test_runner" in content or "Test runner:" in content, (
            "zie-memory step must store test runner"
        )

    def test_memory_step_uses_tags(self):
        content = read(self.COMMAND_PATH)
        assert "tags=" in content or "tags=[" in content, (
            "zie-memory step must use tags for categorization"
        )


# ── AC4: zie-init.md must NOT reference local ~/.claude path manipulation ─────

class TestNoLocalMemoryPath:
    COMMAND_PATH = "commands/zie-init.md"

    def test_no_local_claude_projects_path(self):
        content = read(self.COMMAND_PATH)
        assert "~/.claude/projects" not in content, (
            "zie-init.md must not reference ~/.claude/projects — use zie-memory instead"
        )

    def test_no_encoded_path_logic(self):
        content = read(self.COMMAND_PATH)
        # Should not contain the path encoding logic we removed
        assert "every `/` replaced by `-`" not in content, (
            "zie-init.md must not contain local path encoding logic"
        )
