"""Tests for context-lean-sprint Tasks 2+3: plan-reviewer and impl-reviewer context_bundle."""
from pathlib import Path

PLAN_REVIEWER_PATH = Path(__file__).parents[2] / "skills" / "plan-reviewer" / "SKILL.md"
IMPL_REVIEWER_PATH = Path(__file__).parents[2] / "skills" / "impl-reviewer" / "SKILL.md"


class TestPlanReviewerContextBundle:
    def test_context_bundle_phase_present(self):
        text = PLAN_REVIEWER_PATH.read_text()
        assert "context_bundle" in text, \
            "plan-reviewer must document context_bundle parameter"

    def test_uses_bundle_adrs_when_provided(self):
        text = PLAN_REVIEWER_PATH.read_text()
        assert "context_bundle.adrs" in text or "context_bundle" in text

    def test_fallback_present(self):
        text = PLAN_REVIEWER_PATH.read_text()
        assert "absent" in text.lower() or "fallback" in text.lower() or \
               "backward-compatible" in text.lower()

    def test_review_checklist_unchanged(self):
        text = PLAN_REVIEWER_PATH.read_text()
        assert "TDD structure" in text and "Task granularity" in text, \
            "plan-reviewer Phase 2 checklist must be unchanged"


class TestImplReviewerContextBundle:
    def test_context_bundle_phase_present(self):
        text = IMPL_REVIEWER_PATH.read_text()
        assert "context_bundle" in text, \
            "impl-reviewer must document context_bundle parameter"

    def test_phase1_validates_bundle(self):
        """impl-reviewer Phase 1 validates context_bundle presence."""
        text = IMPL_REVIEWER_PATH.read_text()
        assert "Phase 1" in text and "Validate Context Bundle" in text

    def test_disk_fallback_present(self):
        """If context_bundle absent, fall back to disk reads."""
        text = IMPL_REVIEWER_PATH.read_text()
        assert "fallback" in text.lower() or "absent" in text.lower() or \
               "backward-compatible" in text.lower() or "disk" in text.lower()
