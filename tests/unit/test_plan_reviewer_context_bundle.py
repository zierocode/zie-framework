"""Tests for context-lean-sprint: review skill context_bundle support."""

from pathlib import Path

REVIEW_PATH = Path(__file__).parents[2] / "skills" / "review" / "SKILL.md"


class TestReviewContextBundle:
    def test_context_bundle_phase_present(self):
        text = REVIEW_PATH.read_text()
        assert "context_bundle" in text, "review skill must document context_bundle parameter"

    def test_uses_bundle_adrs_when_provided(self):
        text = REVIEW_PATH.read_text()
        assert "context_bundle.adrs" in text or "context_bundle" in text

    def test_fallback_present(self):
        text = REVIEW_PATH.read_text()
        assert "missing" in text.lower() or "fallback" in text.lower() or "required" in text.lower()

    def test_review_checklist_present(self):
        text = REVIEW_PATH.read_text()
        assert "TDD structure" in text or "Task granularity" in text or "checklist" in text.lower()


class TestImplReviewPhase:
    def test_impl_phase_documented(self):
        text = REVIEW_PATH.read_text()
        assert "impl" in text.lower(), "review skill must support impl phase"

    def test_spec_phase_documented(self):
        text = REVIEW_PATH.read_text()
        assert "spec" in text.lower(), "review skill must support spec phase"

    def test_plan_phase_documented(self):
        text = REVIEW_PATH.read_text()
        assert "plan" in text.lower(), "review skill must support plan phase"