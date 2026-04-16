"""Tests verifying context:fork frontmatter in the unified review skill."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
SKILLS = ROOT / "skills"


def read_frontmatter(skill_name: str) -> str:
    """Return the raw text between the first pair of --- delimiters."""
    text = (SKILLS / skill_name / "SKILL.md").read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, f"{skill_name}/SKILL.md has no frontmatter block"
    return match.group(1)


class TestReviewSkillForkContext:
    def test_has_context_fork(self):
        fm = read_frontmatter("review")
        assert "context: fork" in fm, "review frontmatter must contain 'context: fork'"

    def test_has_allowed_tools(self):
        fm = read_frontmatter("review")
        assert "allowed-tools:" in fm, "review frontmatter must contain 'allowed-tools:'"

    def test_allowed_tools_read(self):
        fm = read_frontmatter("review")
        assert "Read" in fm, "review allowed-tools must include Read"

    def test_allowed_tools_grep(self):
        fm = read_frontmatter("review")
        assert "Grep" in fm, "review allowed-tools must include Grep"

    def test_allowed_tools_glob(self):
        fm = read_frontmatter("review")
        assert "Glob" in fm, "review allowed-tools must include Glob"

    def test_allowed_tools_bash(self):
        fm = read_frontmatter("review")
        assert "Bash" in fm, "review allowed-tools must include Bash (impl phase needs shell access)"

    def test_has_agent_explore(self):
        fm = read_frontmatter("review")
        assert "agent: Explore" in fm, "review frontmatter must contain 'agent: Explore'"


class TestReadFrontmatterHelper:
    def test_raises_on_missing_frontmatter(self, tmp_path, monkeypatch):
        """read_frontmatter must assert-fail on a SKILL.md with no --- block."""
        fake_skill = tmp_path / "no-fm" / "SKILL.md"
        fake_skill.parent.mkdir()
        fake_skill.write_text("# No frontmatter here\n\nJust content.\n")
        monkeypatch.setattr("tests.unit.test_skills_fork_context.SKILLS", tmp_path)
        with pytest.raises(AssertionError, match="no-fm/SKILL.md has no frontmatter block"):
            read_frontmatter("no-fm")

    def test_review_context_fork_is_exact_field(self):
        """'context: fork' must be a standalone field, not a substring."""
        fm = read_frontmatter("review")
        lines = fm.splitlines()
        assert any(line.strip() == "context: fork" for line in lines), (
            "review: 'context: fork' must appear as an exact line in frontmatter"
        )

    def test_review_agent_is_exact_field(self):
        fm = read_frontmatter("review")
        lines = fm.splitlines()
        assert any(line.strip() == "agent: Explore" for line in lines), (
            "review: 'agent: Explore' must appear as an exact line in frontmatter"
        )