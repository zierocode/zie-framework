"""Tests for SKILL.md frontmatter fields: user-invocable, allowed-tools, effort."""
import os

import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def read_frontmatter(skill_name: str) -> dict:
    """Parse YAML frontmatter block from a SKILL.md file."""
    path = os.path.join(REPO_ROOT, "skills", skill_name, "SKILL.md")
    with open(path) as f:
        content = f.read()
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


class TestReviewerSkillsFrontmatter:
    def test_spec_reviewer_user_invocable_false(self):
        fm = read_frontmatter("spec-reviewer")
        assert fm.get("user-invocable") is False, \
            "spec-reviewer must have user-invocable: false"

    def test_spec_reviewer_allowed_tools(self):
        fm = read_frontmatter("spec-reviewer")
        assert fm.get("allowed-tools") == "Read, Grep, Glob", \
            "spec-reviewer must have allowed-tools: Read, Grep, Glob"

    def test_plan_reviewer_user_invocable_false(self):
        fm = read_frontmatter("plan-reviewer")
        assert fm.get("user-invocable") is False, \
            "plan-reviewer must have user-invocable: false"

    def test_plan_reviewer_allowed_tools(self):
        fm = read_frontmatter("plan-reviewer")
        assert fm.get("allowed-tools") == "Read, Grep, Glob", \
            "plan-reviewer must have allowed-tools: Read, Grep, Glob"

    def test_impl_reviewer_user_invocable_false(self):
        fm = read_frontmatter("impl-reviewer")
        assert fm.get("user-invocable") is False, \
            "impl-reviewer must have user-invocable: false"

    def test_impl_reviewer_allowed_tools(self):
        fm = read_frontmatter("impl-reviewer")
        assert fm.get("allowed-tools") == "Read, Grep, Glob, Bash", \
            "impl-reviewer must have allowed-tools: Read, Grep, Glob, Bash"


class TestInternalProcessSkillsFrontmatter:
    def test_tdd_loop_user_invocable_false(self):
        fm = read_frontmatter("tdd-loop")
        assert fm.get("user-invocable") is False, \
            "tdd-loop must have user-invocable: false"

    def test_test_pyramid_user_invocable_false(self):
        fm = read_frontmatter("test-pyramid")
        assert fm.get("user-invocable") is False, \
            "test-pyramid must have user-invocable: false"

    def test_debug_user_invocable_false(self):
        fm = read_frontmatter("debug")
        assert fm.get("user-invocable") is False, \
            "debug must have user-invocable: false"


class TestPlanningSkillsFrontmatter:
    def test_spec_design_effort_high(self):
        fm = read_frontmatter("spec-design")
        assert fm.get("effort") == "high", \
            "spec-design must have effort: high"

    def test_write_plan_effort_low(self):
        fm = read_frontmatter("write-plan")
        assert fm.get("effort") == "low", \
            "write-plan must have effort: low (further reduced from medium per model-write-plan-effort-medium-to-low)"


ALL_SKILLS = [
    "spec-reviewer", "plan-reviewer", "impl-reviewer",
    "tdd-loop", "test-pyramid", "debug",
    "spec-design", "write-plan", "verify",
]


class TestAllSkillsFrontmatterValid:
    def test_all_skills_have_parseable_frontmatter(self):
        """Every SKILL.md must have a valid YAML frontmatter block."""
        for skill in ALL_SKILLS:
            fm = read_frontmatter(skill)
            assert isinstance(fm, dict), \
                f"{skill}/SKILL.md frontmatter must parse to a dict, got {type(fm)}"
            assert "name" in fm, \
                f"{skill}/SKILL.md frontmatter must contain a 'name' field"

    def test_verify_is_user_invocable(self):
        """verify is a user-facing skill — must NOT have user-invocable: false."""
        fm = read_frontmatter("verify")
        assert fm.get("user-invocable") is not False, \
            "verify must NOT have user-invocable: false — it is user-facing"
