"""Tests for the unified review skill's terse output format."""

from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"
REVIEW_SKILL = SKILLS_DIR / "review" / "SKILL.md"


def read_review():
    return REVIEW_SKILL.read_text()


class TestReviewTerseOutput:
    def test_approval_line_is_exactly_approved(self):
        text = read_review()
        assert "✅ APPROVED\n```" in text, "Approval block must end immediately after APPROVED with no extra lines"

    def test_issues_header_present(self):
        assert "❌ Issues Found" in read_review()

    def test_no_prose_before_bullets(self):
        text = read_review()
        assert "❌ Issues Found\n\n1." in text, "Issues block must have no prose between header and first bullet"

    def test_single_line_fix_prompt(self):
        text = read_review()
        assert "Fix these and re-submit for review." in text

    def test_phase_headings_present(self):
        text = read_review()
        assert "## Phase 1" in text
        assert "## Phase 2" in text
        assert "## Phase 3" in text