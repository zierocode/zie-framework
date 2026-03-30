"""Tests for agentic-pipeline-v2 Task 2: zie-plan auto-approve on reviewer APPROVED."""
from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "zie-plan.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestPlanAutoApprove:
    def test_no_explicit_approve_prompt(self):
        """'Approve this plan? (yes / re-draft / drop)' prompt removed — auto-approved."""
        text = cmd_text()
        assert "Approve this plan?" not in text, \
            "zie-plan must not ask 'Approve this plan?' when reviewer returns APPROVED"

    def test_auto_approve_on_reviewer_approved(self):
        """When plan-reviewer returns APPROVED, plan is auto-approved."""
        text = cmd_text()
        assert "auto" in text.lower() or "automatically" in text.lower() or \
               ("APPROVED" in text and "frontmatter" in text.lower()), \
            "zie-plan must document auto-approval on reviewer APPROVED"

    def test_redraft_override_documented(self):
        """User can still override with /zie-plan re-draft."""
        text = cmd_text()
        assert "re-draft" in text, "zie-plan must document re-draft override option"

    def test_drop_override_documented(self):
        """User can still override with /zie-plan drop."""
        text = cmd_text()
        assert "drop" in text, "zie-plan must document drop override option"

    def test_frontmatter_auto_written(self):
        """approved: true frontmatter written automatically on APPROVED."""
        text = cmd_text()
        assert "approved: true" in text, "zie-plan must auto-write approved: true frontmatter"

    def test_roadmap_move_present(self):
        """ROADMAP Next → Ready move still happens."""
        text = cmd_text()
        assert "Ready" in text and "Next" in text, \
            "zie-plan must still move item from Next to Ready"

    def test_issues_found_path_preserved(self):
        """If reviewer returns Issues Found, user is prompted to fix or drop."""
        text = cmd_text()
        assert "Issues" in text or "issues" in text, \
            "zie-plan must handle Issues Found from reviewer (old flow preserved)"
