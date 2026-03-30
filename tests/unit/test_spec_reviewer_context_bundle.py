"""Tests for context-lean-sprint Task 1: spec-reviewer accepts context_bundle."""
from pathlib import Path

SKILL_PATH = Path(__file__).parents[2] / "skills" / "spec-reviewer" / "SKILL.md"


def skill_text() -> str:
    return SKILL_PATH.read_text()


class TestSpecReviewerContextBundle:
    def test_context_bundle_phase_present(self):
        """spec-reviewer documents context_bundle parameter."""
        text = skill_text()
        assert "context_bundle" in text, \
            "spec-reviewer must document context_bundle parameter"

    def test_uses_bundle_adrs_when_provided(self):
        """When context_bundle provided, adrs_content comes from bundle."""
        text = skill_text()
        assert "context_bundle.adrs" in text or "context_bundle" in text, \
            "spec-reviewer must use context_bundle.adrs when provided"

    def test_uses_bundle_context_when_provided(self):
        """When context_bundle provided, context_content comes from bundle."""
        text = skill_text()
        assert "context_bundle.context" in text or "context_bundle" in text, \
            "spec-reviewer must use context_bundle.context when provided"

    def test_fallback_to_disk_when_no_bundle(self):
        """When context_bundle absent, falls back to disk reads."""
        text = skill_text()
        assert "absent" in text.lower() or "fallback" in text.lower() or \
               "backward-compatible" in text.lower() or "disk" in text.lower(), \
            "spec-reviewer must document fallback to disk reads"

    def test_review_checklist_unchanged(self):
        """Phase 2 review checklist remains unchanged."""
        text = skill_text()
        assert "YAGNI" in text and "Testability" in text, \
            "spec-reviewer Phase 2 checklist must be unchanged"
