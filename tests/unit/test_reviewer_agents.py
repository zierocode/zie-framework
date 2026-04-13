"""Tests for agents/spec-reviewer.md, agents/plan-reviewer.md, agents/impl-reviewer.md"""
from pathlib import Path

import yaml

AGENTS_DIR = Path(__file__).parents[2] / "agents"


def load_agent_frontmatter(filename: str) -> dict:
    """Parse YAML frontmatter block from an agent markdown file."""
    path = AGENTS_DIR / filename
    text = path.read_text()
    assert text.startswith("---\n"), f"{filename}: missing opening frontmatter delimiter"
    end = text.index("---\n", 4)
    return yaml.safe_load(text[4:end])


class TestSpecReviewerAgent:
    def test_agent_file_exists(self):
        assert (AGENTS_DIR / "spec-reviewer.md").exists()

    def test_frontmatter_parses(self):
        fm = load_agent_frontmatter("spec-reviewer.md")
        assert isinstance(fm, dict)

    def test_has_isolation_worktree(self):
        fm = load_agent_frontmatter("spec-reviewer.md")
        assert fm.get("isolation") == "worktree", \
            "spec-reviewer must declare isolation: worktree"

    def test_has_allowed_tools(self):
        fm = load_agent_frontmatter("spec-reviewer.md")
        assert "allowed-tools" in fm, "spec-reviewer must have allowed-tools"
        for t in ("Read", "Grep", "Glob"):
            assert t in fm["allowed-tools"], f"missing tool: {t}"

    def test_delegates_to_skill(self):
        text = (AGENTS_DIR / "spec-reviewer.md").read_text()
        assert "Skill(zie-framework:spec-reviewer)" in text


class TestPlanReviewerAgent:
    def test_agent_file_exists(self):
        assert (AGENTS_DIR / "plan-reviewer.md").exists()

    def test_frontmatter_parses(self):
        fm = load_agent_frontmatter("plan-reviewer.md")
        assert isinstance(fm, dict)

    def test_has_isolation_worktree(self):
        fm = load_agent_frontmatter("plan-reviewer.md")
        assert fm.get("isolation") == "worktree", \
            "plan-reviewer must declare isolation: worktree"

    def test_has_allowed_tools(self):
        fm = load_agent_frontmatter("plan-reviewer.md")
        assert "allowed-tools" in fm, "plan-reviewer must have allowed-tools"
        for t in ("Read", "Grep", "Glob"):
            assert t in fm["allowed-tools"], f"missing tool: {t}"

    def test_delegates_to_skill(self):
        text = (AGENTS_DIR / "plan-reviewer.md").read_text()
        assert "Skill(zie-framework:plan-reviewer)" in text


class TestImplReviewerAgent:
    def test_agent_file_exists(self):
        assert (AGENTS_DIR / "impl-reviewer.md").exists()

    def test_frontmatter_parses(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        assert isinstance(fm, dict)

    def test_has_background_true(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        assert fm.get("background") is True, \
            "impl-reviewer must declare background: true"

    def test_no_isolation_worktree(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        assert "isolation" not in fm, \
            "impl-reviewer must NOT have isolation: worktree"

    def test_has_allowed_tools_with_bash(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        assert "allowed-tools" in fm
        tools = fm["allowed-tools"]
        for t in ("Read", "Grep", "Glob", "Bash"):
            assert t in tools, f"missing tool: {t}"

    def test_delegates_to_skill(self):
        text = (AGENTS_DIR / "impl-reviewer.md").read_text()
        assert "Skill(zie-framework:impl-reviewer)" in text


class TestCallerUpdates:
    def test_zie_implement_uses_skill_reviewer(self):
        text = (Path(__file__).parents[2] / "commands" / "implement.md").read_text()
        assert "Skill(zie-framework:impl-reviewer)" in text, \
            "zie-implement.md must invoke impl-reviewer via Skill for HIGH-risk tasks"


class TestComponentsRegistry:
    def test_agents_section_exists(self):
        text = (Path(__file__).parents[2] / "zie-framework" / "project" / "components.md").read_text()
        assert "## Agents" in text, "components.md must have an Agents section"

    def test_all_three_agents_listed(self):
        text = (Path(__file__).parents[2] / "zie-framework" / "project" / "components.md").read_text()
        for agent in ("spec-reviewer", "plan-reviewer", "impl-reviewer"):
            assert agent in text, f"components.md Agents section must list {agent}"
