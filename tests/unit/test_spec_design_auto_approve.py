"""Tests for agentic-pipeline-v2 Task 1: spec-design auto-approve on reviewer APPROVED."""
from pathlib import Path

SKILL_PATH = Path(__file__).parents[2] / "skills" / "spec-design" / "SKILL.md"


def skill_text() -> str:
    return SKILL_PATH.read_text()


class TestSpecDesignAutoApprove:
    def test_no_ask_user_to_review_step(self):
        """Step 8 ('Ask user to review') must be removed — reviewer verdict IS the gate."""
        text = skill_text()
        assert "Ask user to review" not in text, \
            "spec-design must not ask user to review after spec-review APPROVED"

    def test_record_approval_step_present(self):
        """Frontmatter is written automatically when spec-review returns APPROVED."""
        text = skill_text()
        assert "Record approval" in text, \
            "spec-design must still auto-write frontmatter on APPROVED"

    def test_spec_reviewer_loop_intact(self):
        """Spec-reviewer loop (step 5) must remain unchanged."""
        text = skill_text()
        assert "Spec reviewer loop" in text or "spec-review" in text.lower()

    def test_print_handoff_present(self):
        """Handoff block must still be present."""
        text = skill_text()
        assert "Next: Run /plan" in text or "zie-plan" in text

    def test_approved_frontmatter_auto_written(self):
        """frontmatter is written atomically when reviewer returns APPROVED (no user confirmation)."""
        text = skill_text()
        assert "approved: true" in text, "APPROVED frontmatter must still be written"
