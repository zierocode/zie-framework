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
        assert "plan-reviewer" not in skill_text(), \
            "write-plan skill must NOT reference plan-reviewer (belongs in plan.md)"

    def test_standalone_behavior_documented(self):
        assert "--no-memory" in skill_text(), \
            "existing --no-memory flag must remain (standalone behavior unchanged)"

    def test_sprint_handles_inline_plan_review(self):
        """Sprint Phase 1 must invoke plan-reviewer inline (no agent spawn)."""
        t = sprint_text()
        phase1_idx = t.index("PHASE 1")
        phase2_idx = t.index("PHASE 2")
        phase1 = t[phase1_idx:phase2_idx]
        assert "plan-reviewer" in phase1, \
            "Sprint Phase 1 must invoke plan-reviewer inline for autonomous mode"

    def test_sprint_phase1_no_agent_for_plan_review(self):
        """Sprint Phase 1 uses Skill calls not Agent spawns for plan-reviewer."""
        t = sprint_text()
        phase1_idx = t.index("PHASE 1")
        phase2_idx = t.index("PHASE 2")
        phase1 = t[phase1_idx:phase2_idx]
        assert "Skill(zie-framework:plan-reviewer)" in phase1, \
            "Sprint Phase 1 must call plan-reviewer via Skill (not Agent spawn)"
