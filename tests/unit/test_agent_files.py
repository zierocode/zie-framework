"""Tests for agents/ directory files and zie-implement command async reviewer protocol."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
COMMANDS_DIR = REPO_ROOT / "commands"
COMPONENTS_PATH = REPO_ROOT / "zie-framework" / "project" / "components.md"


def _read_frontmatter(path: Path) -> str:
    """Return the raw frontmatter block (between first two --- lines)."""
    text = path.read_text()
    parts = text.split("---")
    assert len(parts) >= 3, f"{path.name}: no frontmatter found"
    return parts[1]


class TestSpecReviewerAgent:
    def test_file_exists(self):
        assert (AGENTS_DIR / "spec-reviewer.md").exists()

    def test_has_isolation_worktree(self):
        fm = _read_frontmatter(AGENTS_DIR / "spec-reviewer.md")
        assert "isolation: worktree" in fm, \
            "spec-reviewer.md must declare isolation: worktree"

    def test_has_allowed_tools(self):
        fm = _read_frontmatter(AGENTS_DIR / "spec-reviewer.md")
        assert "allowed-tools:" in fm

    def test_delegates_to_skill(self):
        text = (AGENTS_DIR / "spec-reviewer.md").read_text()
        assert "Skill(zie-framework:spec-reviewer)" in text


class TestPlanReviewerAgent:
    def test_file_exists(self):
        assert (AGENTS_DIR / "plan-reviewer.md").exists()

    def test_has_isolation_worktree(self):
        fm = _read_frontmatter(AGENTS_DIR / "plan-reviewer.md")
        assert "isolation: worktree" in fm, \
            "plan-reviewer.md must declare isolation: worktree"

    def test_has_allowed_tools(self):
        fm = _read_frontmatter(AGENTS_DIR / "plan-reviewer.md")
        assert "allowed-tools:" in fm

    def test_delegates_to_skill(self):
        text = (AGENTS_DIR / "plan-reviewer.md").read_text()
        assert "Skill(zie-framework:plan-reviewer)" in text


class TestImplReviewerAgent:
    def test_file_exists(self):
        assert (AGENTS_DIR / "impl-reviewer.md").exists()

    def test_has_background_true(self):
        fm = _read_frontmatter(AGENTS_DIR / "impl-reviewer.md")
        assert "background: true" in fm, \
            "impl-reviewer.md must declare background: true"

    def test_no_isolation_worktree(self):
        fm = _read_frontmatter(AGENTS_DIR / "impl-reviewer.md")
        assert "isolation: worktree" not in fm, \
            "impl-reviewer must NOT have isolation: worktree — it needs live files"

    def test_has_bash_in_allowed_tools(self):
        fm = _read_frontmatter(AGENTS_DIR / "impl-reviewer.md")
        assert "Bash" in fm, \
            "impl-reviewer must allow Bash to run make test*"

    def test_delegates_to_skill(self):
        text = (AGENTS_DIR / "impl-reviewer.md").read_text()
        assert "Skill(zie-framework:impl-reviewer)" in text


class TestZieImplementCommand:
    def _read_command(self):
        return (COMMANDS_DIR / "implement.md").read_text()

    def test_inline_review_for_high_risk(self):
        text = self._read_command()
        assert "inline" in text.lower() and "HIGH" in text, \
            "zie-implement must describe inline review gated on HIGH risk"

    def test_no_background_agent_spawn(self):
        text = self._read_command()
        assert "@agent-impl-reviewer" not in text, \
            "zie-implement must not spawn @agent-impl-reviewer background agent"

    def test_auto_fix_protocol_present(self):
        t = text = self._read_command()
        t = text.lower()
        assert "auto-fix" in t or ("fix" in t and "retry" in t), \
            "zie-implement must describe auto-fix protocol after review issues"

    def test_interrupt_on_fix_failure(self):
        t = self._read_command().lower()
        assert "interrupt" in t or "surface" in t, \
            "zie-implement must interrupt when auto-fix fails"

    def test_impl_reviewer_invoked_as_skill(self):
        text = self._read_command()
        assert "Skill(zie-framework:impl-reviewer)" in text, \
            "zie-implement must invoke impl-reviewer via Skill(zie-framework:impl-reviewer)"


class TestComponentsDocAgents:
    def _read(self):
        return COMPONENTS_PATH.read_text()

    def test_agents_section_exists(self):
        assert "## Agents" in self._read(), \
            "components.md must have an Agents section"

    def test_spec_reviewer_documented(self):
        assert "spec-reviewer" in self._read()

    def test_plan_reviewer_documented(self):
        assert "plan-reviewer" in self._read()

    def test_impl_reviewer_documented(self):
        assert "impl-reviewer" in self._read()

    def test_isolation_worktree_explained(self):
        assert "isolation: worktree" in self._read(), \
            "components.md must explain the isolation: worktree field"

    def test_background_true_explained(self):
        assert "background: true" in self._read(), \
            "components.md must explain the background: true field"
