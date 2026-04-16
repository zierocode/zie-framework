"""Tests for the consolidated review skill and caller updates."""

from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"
AGENTS_DIR = Path(__file__).parents[2] / "agents"


class TestReviewSkill:
    def test_skill_dir_exists(self):
        assert (SKILLS_DIR / "review").is_dir()

    def test_skill_md_exists(self):
        assert (SKILLS_DIR / "review" / "SKILL.md").exists()

    def test_skill_supports_all_phases(self):
        text = (SKILLS_DIR / "review" / "SKILL.md").read_text()
        for phase in ("spec", "plan", "impl"):
            assert phase in text.lower(), f"review skill must support {phase} phase"


class TestOldReviewerAgentsRemoved:
    def test_spec_reviewer_agent_removed(self):
        assert not (AGENTS_DIR / "spec-review.md").exists(), "spec-review.md agent should be removed (merged into review skill)"

    def test_plan_reviewer_agent_removed(self):
        assert not (AGENTS_DIR / "plan-review.md").exists(), "plan-review.md agent should be removed (merged into review skill)"

    def test_impl_reviewer_agent_removed(self):
        assert not (AGENTS_DIR / "impl-review.md").exists(), "impl-review.md agent should be removed (merged into review skill)"


class TestCallerUpdates:
    def test_zie_implement_uses_review_skill(self):
        text = (Path(__file__).parents[2] / "commands" / "implement.md").read_text()
        assert "Skill(zie-framework:review" in text, (
            "implement.md must invoke review via Skill(zie-framework:review)"
        )


class TestComponentsRegistry:
    def test_agents_section_exists(self):
        text = (Path(__file__).parents[2] / "zie-framework" / "project" / "components.md").read_text()
        assert "## Agents" in text, "components.md must have an Agents section"

    def test_review_skill_listed(self):
        text = (Path(__file__).parents[2] / "zie-framework" / "project" / "components.md").read_text()
        assert "review" in text, "components.md must list the review skill"