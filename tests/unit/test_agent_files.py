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
        return (COMMANDS_DIR / "zie-implement.md").read_text()

    def test_spawns_background_agent(self):
        text = self._read_command()
        assert "@agent-impl-reviewer" in text, \
            "zie-implement must invoke @agent-impl-reviewer (agent file, not skill)"

    def test_deferred_check_protocol_present(self):
        text = self._read_command()
        assert "reviewer_status" in text, \
            "zie-implement must check reviewer_status for deferred results"

    def test_pending_approved_issues_states_covered(self):
        text = self._read_command()
        for state in ("pending", "approved", "issues_found"):
            assert state in text, \
                f"zie-implement must handle reviewer_status: {state}"

    def test_final_wait_before_verify(self):
        text = self._read_command()
        assert "final-wait" in text or "still-pending" in text or \
               "wait for any" in text.lower(), \
            "zie-implement must wait for pending reviewers before verify step"

    def test_120s_timeout_surfaced(self):
        text = self._read_command()
        assert "120" in text, \
            "zie-implement must surface the 120s timeout threshold"

    def test_max_3_iterations_preserved(self):
        text = self._read_command()
        assert "3" in text and "iteration" in text.lower(), \
            "zie-implement must preserve max-3-iteration gate"

    def test_no_inline_impl_reviewer_skill(self):
        text = self._read_command()
        assert "Skill(zie-framework:impl-reviewer)" not in text, \
            "inline Skill call must be replaced by @agent-impl-reviewer invocation"


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
