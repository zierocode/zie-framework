from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"


class TestSpecReviewerTerseOutput:
    def _text(self) -> str:
        return (SKILLS_DIR / "spec-reviewer" / "SKILL.md").read_text()

    def test_approval_line_is_exactly_approved(self):
        text = self._text()
        assert "✅ APPROVED\n```" in text, \
            "Approval block must end immediately after '✅ APPROVED' with no extra lines"

    def test_no_verbose_approval_prose(self):
        text = self._text()
        assert "Spec is complete, clear, and scoped correctly." not in text, \
            "Verbose approval prose must be removed"

    def test_issues_header_present(self):
        text = self._text()
        assert "❌ Issues Found" in text

    def test_no_prose_before_bullets(self):
        text = self._text()
        assert "❌ Issues Found\n\n1." in text, \
            "Issues block must have no prose between header and first bullet"

    def test_single_line_fix_prompt(self):
        text = self._text()
        assert "Fix these and re-submit for review." in text

    def test_phase_headings_unchanged(self):
        text = self._text()
        assert "## Phase 1" in text
        assert "## Phase 2" in text
        assert "## Phase 3" in text


class TestPlanReviewerTerseOutput:
    def _text(self) -> str:
        return (SKILLS_DIR / "plan-reviewer" / "SKILL.md").read_text()

    def test_approval_line_is_exactly_approved(self):
        text = self._text()
        assert "✅ APPROVED\n```" in text, \
            "Approval block must end immediately after '✅ APPROVED' with no extra lines"

    def test_no_verbose_approval_prose(self):
        text = self._text()
        assert "Plan is complete, TDD-structured, and covers the spec." not in text, \
            "Verbose approval prose must be removed"

    def test_issues_header_present(self):
        text = self._text()
        assert "❌ Issues Found" in text

    def test_no_prose_before_bullets(self):
        text = self._text()
        assert "❌ Issues Found\n\n1." in text, \
            "Issues block must have no prose between header and first bullet"

    def test_single_line_fix_prompt(self):
        text = self._text()
        assert "Fix these and re-submit for review." in text

    def test_phase_headings_unchanged(self):
        text = self._text()
        assert "## Phase 1" in text
        assert "## Phase 2" in text
        assert "## Phase 3" in text


class TestImplReviewerTerseOutput:
    def _text(self) -> str:
        return (SKILLS_DIR / "impl-reviewer" / "SKILL.md").read_text()

    def test_approval_line_is_exactly_approved(self):
        text = self._text()
        assert "✅ APPROVED\n```" in text, \
            "Approval block must end immediately after '✅ APPROVED' with no extra lines"

    def test_no_verbose_approval_prose(self):
        text = self._text()
        assert "Implementation satisfies AC. Tests present and passing." not in text, \
            "Verbose approval prose must be removed"

    def test_issues_header_present(self):
        text = self._text()
        assert "❌ Issues Found" in text

    def test_no_prose_before_bullets(self):
        text = self._text()
        assert "❌ Issues Found\n\n1." in text, \
            "Issues block must have no prose between header and first bullet"

    def test_single_line_fix_prompt(self):
        text = self._text()
        assert "Fix these, re-run make test-unit, and re-invoke impl-reviewer." in text

    def test_phase_headings_unchanged(self):
        text = self._text()
        assert "## Phase 1" in text
        assert "## Phase 2" in text
        assert "## Phase 3" in text
