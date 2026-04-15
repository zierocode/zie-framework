"""Tests for agents/spec-review.md, agents/plan-review.md, agents/impl-review.md"""
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
        assert (AGENTS_DIR / "spec-review.md").exists()

    def test_frontmatter_parses(self):
        fm = load_agent_frontmatter("spec-review.md")
        assert isinstance(fm, dict)

    def test_has_isolation_worktree(self):
        fm = load_agent_frontmatter("spec-review.md")
        assert fm.get("isolation") == "worktree", \
            "spec-review must declare isolation: worktree"

    def test_has_allowed_tools(self):
        fm = load_agent_frontmatter("spec-review.md")
        assert "allowed-tools" in fm, "spec-review must have allowed-tools"
        for t in ("Read", "Grep", "Glob"):
            assert t in fm["allowed-tools"], f"missing tool: {t}"

    def test_delegates_to_skill(self):
        text = (AGENTS_DIR / "spec-review.md").read_text()
        assert "Skill(zie-framework:spec-review)" in text


class TestPlanReviewerAgent:
    def test_agent_file_exists(self):
        assert (AGENTS_DIR / "plan-review.md").exists()

    def test_frontmatter_parses(self):
        fm = load_agent_frontmatter("plan-review.md")
        assert isinstance(fm, dict)

    def test_has_isolation_worktree(self):
        fm = load_agent_frontmatter("plan-review.md")
        assert fm.get("isolation") == "worktree", \
            "plan-review must declare isolation: worktree"

    def test_has_allowed_tools(self):
        fm = load_agent_frontmatter("plan-review.md")
        assert "allowed-tools" in fm, "plan-review must have allowed-tools"
        for t in ("Read", "Grep", "Glob"):
            assert t in fm["allowed-tools"], f"missing tool: {t}"

    def test_delegates_to_skill(self):
        text = (AGENTS_DIR / "plan-review.md").read_text()
        assert "Skill(zie-framework:plan-review)" in text


class TestImplReviewerAgent:
    def test_agent_file_exists(self):
        assert (AGENTS_DIR / "impl-review.md").exists()

    def test_frontmatter_parses(self):
        fm = load_agent_frontmatter("impl-review.md")
        assert isinstance(fm, dict)

    def test_has_background_true(self):
        fm = load_agent_frontmatter("impl-review.md")
        assert fm.get("background") is True, \
            "impl-review must declare background: true"

    def test_no_isolation_worktree(self):
        fm = load_agent_frontmatter("impl-review.md")
        assert "isolation" not in fm, \
            "impl-review must NOT have isolation: worktree"

    def test_has_allowed_tools_with_bash(self):
        fm = load_agent_frontmatter("impl-review.md")
        assert "allowed-tools" in fm
        tools = fm["allowed-tools"]
        for t in ("Read", "Grep", "Glob", "Bash"):
            assert t in tools, f"missing tool: {t}"

    def test_delegates_to_skill(self):
        text = (AGENTS_DIR / "impl-review.md").read_text()
        assert "Skill(zie-framework:impl-review)" in text


class TestCallerUpdates:
    def test_zie_implement_uses_skill_reviewer(self):
        text = (Path(__file__).parents[2] / "commands" / "implement.md").read_text()
        assert "Skill(zie-framework:impl-review)" in text, \
            "zie-implement.md must invoke impl-review via Skill for HIGH-risk tasks"


class TestComponentsRegistry:
    def test_agents_section_exists(self):
        text = (Path(__file__).parents[2] / "zie-framework" / "project" / "components.md").read_text()
        assert "## Agents" in text, "components.md must have an Agents section"

    def test_all_three_agents_listed(self):
        text = (Path(__file__).parents[2] / "zie-framework" / "project" / "components.md").read_text()
        for agent in ("spec-review", "plan-review", "impl-review"):
            assert agent in text, f"components.md Agents section must list {agent}"
