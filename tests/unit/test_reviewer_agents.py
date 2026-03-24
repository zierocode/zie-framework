"""Tests for agents/spec-reviewer.md, agents/plan-reviewer.md, agents/impl-reviewer.md"""
import yaml
from pathlib import Path

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

    def test_required_fields_present(self):
        fm = load_agent_frontmatter("spec-reviewer.md")
        for field in ("name", "description", "model", "tools", "permissionMode", "memory", "user-invocable"):
            assert field in fm, f"missing field: {field}"

    def test_model_is_haiku(self):
        fm = load_agent_frontmatter("spec-reviewer.md")
        assert fm["model"] == "haiku"

    def test_memory_is_project(self):
        fm = load_agent_frontmatter("spec-reviewer.md")
        assert fm["memory"] == "project"

    def test_permission_mode_is_plan(self):
        fm = load_agent_frontmatter("spec-reviewer.md")
        assert fm["permissionMode"] == "plan"

    def test_user_invocable_is_false(self):
        fm = load_agent_frontmatter("spec-reviewer.md")
        assert fm["user-invocable"] is False

    def test_tools_contains_required(self):
        fm = load_agent_frontmatter("spec-reviewer.md")
        tools = fm["tools"]
        for t in ("Read", "Grep", "Glob"):
            assert t in tools, f"missing tool: {t}"

    def test_body_contains_phase_headings(self):
        text = (AGENTS_DIR / "spec-reviewer.md").read_text()
        assert "Phase 1" in text
        assert "Phase 2" in text
        assert "Phase 3" in text


class TestPlanReviewerAgent:
    def test_agent_file_exists(self):
        assert (AGENTS_DIR / "plan-reviewer.md").exists()

    def test_frontmatter_parses(self):
        fm = load_agent_frontmatter("plan-reviewer.md")
        assert isinstance(fm, dict)

    def test_required_fields_present(self):
        fm = load_agent_frontmatter("plan-reviewer.md")
        for field in ("name", "description", "model", "tools", "permissionMode", "memory", "user-invocable"):
            assert field in fm, f"missing field: {field}"

    def test_model_is_haiku(self):
        fm = load_agent_frontmatter("plan-reviewer.md")
        assert fm["model"] == "haiku"

    def test_memory_is_project(self):
        fm = load_agent_frontmatter("plan-reviewer.md")
        assert fm["memory"] == "project"

    def test_permission_mode_is_plan(self):
        fm = load_agent_frontmatter("plan-reviewer.md")
        assert fm["permissionMode"] == "plan"

    def test_user_invocable_is_false(self):
        fm = load_agent_frontmatter("plan-reviewer.md")
        assert fm["user-invocable"] is False

    def test_tools_contains_required(self):
        fm = load_agent_frontmatter("plan-reviewer.md")
        tools = fm["tools"]
        for t in ("Read", "Grep", "Glob"):
            assert t in tools, f"missing tool: {t}"

    def test_body_contains_phase_headings(self):
        text = (AGENTS_DIR / "plan-reviewer.md").read_text()
        assert "Phase 1" in text
        assert "Phase 2" in text
        assert "Phase 3" in text


class TestImplReviewerAgent:
    def test_agent_file_exists(self):
        assert (AGENTS_DIR / "impl-reviewer.md").exists()

    def test_frontmatter_parses(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        assert isinstance(fm, dict)

    def test_required_fields_present(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        for field in ("name", "description", "model", "tools", "permissionMode", "memory", "user-invocable"):
            assert field in fm, f"missing field: {field}"

    def test_model_is_haiku(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        assert fm["model"] == "haiku"

    def test_memory_is_project(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        assert fm["memory"] == "project"

    def test_permission_mode_is_plan(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        assert fm["permissionMode"] == "plan"

    def test_user_invocable_is_false(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        assert fm["user-invocable"] is False

    def test_tools_contains_read_grep_glob(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        tools = fm["tools"]
        for t in ("Read", "Grep", "Glob"):
            assert t in tools, f"missing tool: {t}"

    def test_tools_contains_bash_scoped(self):
        fm = load_agent_frontmatter("impl-reviewer.md")
        tools = fm["tools"]
        assert "Bash(make test*)" in tools, \
            "impl-reviewer Bash tool must be scoped to 'make test*'"

    def test_body_contains_phase_headings(self):
        text = (AGENTS_DIR / "impl-reviewer.md").read_text()
        assert "Phase 1" in text
        assert "Phase 2" in text
        assert "Phase 3" in text


class TestCallerUpdates:
    def test_spec_design_skill_references_agent(self):
        text = (Path(__file__).parents[2] / "skills" / "spec-design" / "SKILL.md").read_text()
        assert "@agent-spec-reviewer" in text, \
            "spec-design SKILL.md must reference @agent-spec-reviewer"

    def test_spec_design_skill_has_fallback_comment(self):
        text = (Path(__file__).parents[2] / "skills" / "spec-design" / "SKILL.md").read_text()
        assert "fallback: Skill(zie-framework:spec-reviewer)" in text, \
            "spec-design SKILL.md must have fallback comment"

    def test_zie_plan_command_references_agent(self):
        text = (Path(__file__).parents[2] / "commands" / "zie-plan.md").read_text()
        assert "@agent-plan-reviewer" in text, \
            "zie-plan.md must reference @agent-plan-reviewer"

    def test_zie_plan_command_has_fallback_comment(self):
        text = (Path(__file__).parents[2] / "commands" / "zie-plan.md").read_text()
        assert "fallback: Skill(zie-framework:plan-reviewer)" in text, \
            "zie-plan.md must have fallback comment"

    def test_zie_implement_command_references_agent(self):
        text = (Path(__file__).parents[2] / "commands" / "zie-implement.md").read_text()
        assert "@agent-impl-reviewer" in text, \
            "zie-implement.md must reference @agent-impl-reviewer"

    def test_zie_implement_command_has_fallback_comment(self):
        text = (Path(__file__).parents[2] / "commands" / "zie-implement.md").read_text()
        assert "fallback: Skill(zie-framework:impl-reviewer)" in text, \
            "zie-implement.md must have fallback comment"


class TestComponentsRegistry:
    def test_agents_section_exists(self):
        text = (Path(__file__).parents[2] / "zie-framework" / "project" / "components.md").read_text()
        assert "## Agents" in text, "components.md must have an Agents section"

    def test_all_three_agents_listed(self):
        text = (Path(__file__).parents[2] / "zie-framework" / "project" / "components.md").read_text()
        for agent in ("spec-reviewer", "plan-reviewer", "impl-reviewer"):
            assert agent in text, f"components.md Agents section must list {agent}"
