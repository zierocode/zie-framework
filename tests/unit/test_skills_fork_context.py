"""Tests verifying context:fork frontmatter in reviewer skills."""
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


class TestSpecReviewerForkContext:
    def test_has_context_fork(self):
        fm = read_frontmatter("spec-reviewer")
        assert "context: fork" in fm, \
            "spec-reviewer frontmatter must contain 'context: fork'"

    def test_has_agent_explore(self):
        fm = read_frontmatter("spec-reviewer")
        assert "agent: Explore" in fm, \
            "spec-reviewer frontmatter must contain 'agent: Explore'"

    def test_has_allowed_tools(self):
        fm = read_frontmatter("spec-reviewer")
        assert "allowed-tools:" in fm, \
            "spec-reviewer frontmatter must contain 'allowed-tools:'"

    def test_allowed_tools_read(self):
        fm = read_frontmatter("spec-reviewer")
        assert "Read" in fm, \
            "spec-reviewer allowed-tools must include Read"

    def test_allowed_tools_grep(self):
        fm = read_frontmatter("spec-reviewer")
        assert "Grep" in fm, \
            "spec-reviewer allowed-tools must include Grep"

    def test_allowed_tools_glob(self):
        fm = read_frontmatter("spec-reviewer")
        assert "Glob" in fm, \
            "spec-reviewer allowed-tools must include Glob"

    def test_no_bash_in_allowed_tools(self):
        fm = read_frontmatter("spec-reviewer")
        assert "Bash" not in fm, \
            "spec-reviewer is Explore agent — Bash must not appear in frontmatter"


class TestPlanReviewerForkContext:
    def test_has_context_fork(self):
        fm = read_frontmatter("plan-reviewer")
        assert "context: fork" in fm, \
            "plan-reviewer frontmatter must contain 'context: fork'"

    def test_has_agent_explore(self):
        fm = read_frontmatter("plan-reviewer")
        assert "agent: Explore" in fm, \
            "plan-reviewer frontmatter must contain 'agent: Explore'"

    def test_has_allowed_tools(self):
        fm = read_frontmatter("plan-reviewer")
        assert "allowed-tools:" in fm, \
            "plan-reviewer frontmatter must contain 'allowed-tools:'"

    def test_allowed_tools_read(self):
        fm = read_frontmatter("plan-reviewer")
        assert "Read" in fm, \
            "plan-reviewer allowed-tools must include Read"

    def test_allowed_tools_grep(self):
        fm = read_frontmatter("plan-reviewer")
        assert "Grep" in fm, \
            "plan-reviewer allowed-tools must include Grep"

    def test_allowed_tools_glob(self):
        fm = read_frontmatter("plan-reviewer")
        assert "Glob" in fm, \
            "plan-reviewer allowed-tools must include Glob"

    def test_no_bash_in_allowed_tools(self):
        fm = read_frontmatter("plan-reviewer")
        assert "Bash" not in fm, \
            "plan-reviewer is Explore agent — Bash must not appear in frontmatter"


class TestImplReviewerForkContext:
    def test_has_context_fork(self):
        fm = read_frontmatter("impl-reviewer")
        assert "context: fork" in fm, \
            "impl-reviewer frontmatter must contain 'context: fork'"

    def test_has_agent_general_purpose(self):
        fm = read_frontmatter("impl-reviewer")
        assert "agent: general-purpose" in fm, \
            "impl-reviewer frontmatter must contain 'agent: general-purpose'"

    def test_not_agent_explore(self):
        fm = read_frontmatter("impl-reviewer")
        assert "agent: Explore" not in fm, \
            "impl-reviewer must use general-purpose agent, not Explore"

    def test_has_allowed_tools(self):
        fm = read_frontmatter("impl-reviewer")
        assert "allowed-tools:" in fm, \
            "impl-reviewer frontmatter must contain 'allowed-tools:'"

    def test_allowed_tools_read(self):
        fm = read_frontmatter("impl-reviewer")
        assert "Read" in fm, \
            "impl-reviewer allowed-tools must include Read"

    def test_allowed_tools_grep(self):
        fm = read_frontmatter("impl-reviewer")
        assert "Grep" in fm, \
            "impl-reviewer allowed-tools must include Grep"

    def test_allowed_tools_glob(self):
        fm = read_frontmatter("impl-reviewer")
        assert "Glob" in fm, \
            "impl-reviewer allowed-tools must include Glob"

    def test_allowed_tools_bash(self):
        fm = read_frontmatter("impl-reviewer")
        assert "Bash" in fm, \
            "impl-reviewer allowed-tools must include Bash (general-purpose agent needs shell access)"


class TestReadFrontmatterHelper:
    def test_raises_on_missing_frontmatter(self, tmp_path, monkeypatch):
        """read_frontmatter must assert-fail on a SKILL.md with no --- block."""
        fake_skill = tmp_path / "no-fm" / "SKILL.md"
        fake_skill.parent.mkdir()
        fake_skill.write_text("# No frontmatter here\n\nJust content.\n")
        monkeypatch.setattr(
            "tests.unit.test_skills_fork_context.SKILLS", tmp_path
        )
        with pytest.raises(AssertionError, match="no-fm/SKILL.md has no frontmatter block"):
            read_frontmatter("no-fm")

    def test_spec_reviewer_context_fork_is_exact_field(self):
        """'context: fork' must be a standalone field, not a substring."""
        fm = read_frontmatter("spec-reviewer")
        lines = fm.splitlines()
        assert any(line.strip() == "context: fork" for line in lines), \
            "spec-reviewer: 'context: fork' must appear as an exact line in frontmatter"

    def test_plan_reviewer_context_fork_is_exact_field(self):
        fm = read_frontmatter("plan-reviewer")
        lines = fm.splitlines()
        assert any(line.strip() == "context: fork" for line in lines), \
            "plan-reviewer: 'context: fork' must appear as an exact line in frontmatter"

    def test_impl_reviewer_context_fork_is_exact_field(self):
        fm = read_frontmatter("impl-reviewer")
        lines = fm.splitlines()
        assert any(line.strip() == "context: fork" for line in lines), \
            "impl-reviewer: 'context: fork' must appear as an exact line in frontmatter"

    def test_spec_reviewer_agent_is_exact_field(self):
        fm = read_frontmatter("spec-reviewer")
        lines = fm.splitlines()
        assert any(line.strip() == "agent: Explore" for line in lines), \
            "spec-reviewer: 'agent: Explore' must appear as an exact line in frontmatter"

    def test_plan_reviewer_agent_is_exact_field(self):
        fm = read_frontmatter("plan-reviewer")
        lines = fm.splitlines()
        assert any(line.strip() == "agent: Explore" for line in lines), \
            "plan-reviewer: 'agent: Explore' must appear as an exact line in frontmatter"

    def test_impl_reviewer_agent_is_exact_field(self):
        fm = read_frontmatter("impl-reviewer")
        lines = fm.splitlines()
        assert any(line.strip() == "agent: general-purpose" for line in lines), \
            "impl-reviewer: 'agent: general-purpose' must appear as an exact line in frontmatter"
