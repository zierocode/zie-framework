from pathlib import Path

SKILL = Path(__file__).parents[2] / "skills" / "write-plan" / "SKILL.md"
SPRINT = Path(__file__).parents[2] / "commands" / "sprint.md"


def skill_text():
    return SKILL.read_text()


def sprint_text():
    return SPRINT.read_text()


class TestWritePlanAutonomousMode:
    def test_plan_reviewer_not_in_write_plan_skill(self):
        """ADR: reviewer gate belongs in plan.md, not write-plan skill."""
        assert "plan-review" not in skill_text(), "write-plan skill must NOT reference plan-review (belongs in plan.md)"

    def test_standalone_behavior_documented(self):
        assert "--no-memory" in skill_text(), "existing --no-memory flag must remain (standalone behavior unchanged)"

    def test_sprint_handles_inline_plan_review(self):
        """Sprint Phase 1 must invoke review inline (no agent spawn)."""
        t = sprint_text()
        phase1_idx = t.index("PHASE 1")
        phase2_idx = t.index("PHASE 2")
        phase1 = t[phase1_idx:phase2_idx]
        assert "review" in phase1.lower(), "Sprint Phase 1 must invoke review inline for autonomous mode"

    def test_sprint_phase1_no_agent_for_plan_review(self):
        """Sprint Phase 1 uses Skill calls not Agent spawns for review."""
        t = sprint_text()
        phase1_idx = t.index("PHASE 1")
        phase2_idx = t.index("PHASE 2")
        phase1 = t[phase1_idx:phase2_idx]
        assert "Skill(zie-framework:review" in phase1, (
            "Sprint Phase 1 must call review via Skill (not Agent spawn)"
        )
