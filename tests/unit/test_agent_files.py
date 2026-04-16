"""Tests for agents/ directory files and zie-implement command."""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
COMMANDS_DIR = REPO_ROOT / "commands"
COMPONENTS_PATH = REPO_ROOT / "zie-framework" / "project" / "components.md"
SKILLS_DIR = REPO_ROOT / "skills"


def _read_frontmatter(path: Path) -> str:
    """Return the raw frontmatter block (between first two --- lines)."""
    text = path.read_text()
    parts = text.split("---")
    assert len(parts) >= 3, f"{path.name}: no frontmatter found"
    return parts[1]


class TestBuilderAgent:
    def test_file_exists(self):
        assert (AGENTS_DIR / "builder.md").exists()

    def test_delegates_to_skill(self):
        text = (AGENTS_DIR / "builder.md").read_text()
        assert "Skill(zie-framework:tdd-loop" in text


class TestAuditorAgent:
    def test_file_exists(self):
        assert (AGENTS_DIR / "auditor.md").exists()

    def test_read_only_contract(self):
        text = (AGENTS_DIR / "auditor.md").read_text()
        assert "read-only" in text.lower() or "Read-Only" in text


class TestReviewSkill:
    """Parametric review skill (merged from spec-review, plan-review, impl-review)."""

    def test_skill_dir_exists(self):
        assert (SKILLS_DIR / "review").is_dir()

    def test_skill_md_exists(self):
        assert (SKILLS_DIR / "review" / "SKILL.md").exists()

    def test_skill_has_review_types(self):
        text = (SKILLS_DIR / "review" / "SKILL.md").read_text()
        assert "spec" in text.lower() or "plan" in text.lower() or "impl" in text.lower()


class TestZieImplementCommand:
    def _read_command(self):
        return (COMMANDS_DIR / "implement.md").read_text()

    def test_inline_review_for_high_risk(self):
        text = self._read_command()
        assert "inline" in text.lower() and "HIGH" in text, (
            "zie-implement must describe inline review gated on HIGH risk"
        )

    def test_no_background_agent_spawn(self):
        text = self._read_command()
        assert "@agent-impl-review" not in text, "zie-implement must not spawn @agent-impl-review background agent"

    def test_auto_fix_protocol_present(self):
        t = self._read_command().lower()
        assert "auto-fix" in t or ("fix" in t and "retry" in t), (
            "zie-implement must describe auto-fix protocol after review issues"
        )

    def test_interrupt_on_fix_failure(self):
        t = self._read_command().lower()
        assert "interrupt" in t or "surface" in t, "zie-implement must interrupt when auto-fix fails"

    def test_impl_reviewer_invoked_as_skill(self):
        text = self._read_command()
        assert "Skill(zie-framework:impl-review)" in text or "Skill(zie-framework:review" in text, (
            "zie-implement must invoke review via Skill()"
        )


class TestComponentsDocAgents:
    def _read(self):
        return COMPONENTS_PATH.read_text()

    def test_agents_section_exists(self):
        assert "## Agents" in self._read(), "components.md must have an Agents section"

    def test_review_skill_documented(self):
        assert "review" in self._read(), "components.md must document the review skill"

    def test_isolation_worktree_explained(self):
        assert "isolation: worktree" in self._read(), "components.md must explain the isolation: worktree field"

    def test_background_true_explained(self):
        assert "background: true" in self._read(), "components.md must explain the background: true field"