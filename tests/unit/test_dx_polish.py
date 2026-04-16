"""Tests for dx-polish: pipeline indicator, reviewer next-steps, task sizing guidance."""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text()


class TestZieStatusPipeline:
    def test_pipeline_indicator_present(self):
        text = read("commands/status.md")
        assert "Pipeline" in text or "pipeline" in text.lower(), "zie-status must have pipeline stage indicator"

    def test_pipeline_stages_documented(self):
        text = read("commands/status.md")
        for stage in ["backlog", "spec", "plan", "implement", "release", "retro"]:
            assert stage in text, f"pipeline indicator must show '{stage}' stage"

    def test_pipeline_uses_checkmarks(self):
        text = read("commands/status.md")
        assert "✓" in text or "▶" in text, "pipeline indicator must use ✓/▶ symbols"

    def test_pipeline_only_when_active(self):
        text = read("commands/status.md")
        assert "Now lane is empty" in text or "empty" in text.lower(), (
            "pipeline indicator must be skipped when no active feature"
        )


class TestReviewerNextSteps:
    def test_review_skill_max_iterations_block(self):
        text = read("skills/review/SKILL.md")
        assert "Max" in text and "iteration" in text.lower(), (
            "review skill must have max iterations next-steps block"
        )

    def test_review_skill_next_steps_actionable(self):
        text = read("skills/review/SKILL.md")
        assert "Next steps:" in text or "next steps" in text.lower(), (
            "review skill must provide next steps on max iterations"
        )

    def test_review_skill_plan_large_plan_warning(self):
        text = read("skills/review/SKILL.md")
        assert "15 tasks" in text or ">15" in text or "Large plan" in text, (
            "review skill (plan phase) must warn when plan has >15 tasks"
        )


class TestTaskSizingGuidance:
    def test_write_plan_has_sizing_guidance(self):
        text = read("skills/write-plan/SKILL.md")
        assert "Task Sizing" in text or "task sizing" in text.lower(), (
            "write-plan must have task sizing guidance section"
        )

    def test_sizing_tiers_present(self):
        text = read("skills/write-plan/SKILL.md")
        for tier in ["S", "M", "L"]:
            assert tier in text, f"write-plan must document '{tier}' size tier"

    def test_large_plan_warning(self):
        text = read("skills/write-plan/SKILL.md")
        assert ">15" in text or "15 tasks" in text or "too large" in text.lower(), (
            "write-plan must warn about plans larger than 15 tasks"
        )