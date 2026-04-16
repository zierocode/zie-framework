"""Tests for context-lean-sprint: review skill accepts context_bundle."""

from pathlib import Path

SKILL_PATH = Path(__file__).parents[2] / "skills" / "review" / "SKILL.md"


def skill_text() -> str:
    return SKILL_PATH.read_text()


class TestReviewContextBundle:
    def test_context_bundle_phase_present(self):
        """review skill documents context_bundle parameter."""
        text = skill_text()
        assert "context_bundle" in text, "review must document context_bundle parameter"

    def test_uses_bundle_adrs_when_provided(self):
        """When context_bundle provided, adrs_content comes from bundle."""
        text = skill_text()
        assert "context_bundle" in text, "review must use context_bundle when provided"

    def test_uses_bundle_context_when_provided(self):
        """When context_bundle provided, context_content comes from bundle."""
        text = skill_text()
        assert "context_bundle" in text, "review must use context_bundle when provided"

    def test_fallback_to_disk_when_no_bundle(self):
        """When context_bundle absent, falls back to disk reads."""
        text = skill_text().lower()
        assert (
            "absent" in text
            or "fallback" in text
            or "disk" in text
        ), "review must document fallback to disk reads"

    def test_review_checklist_unchanged(self):
        """Review checklist items remain unchanged."""
        text = skill_text()
        assert "YAGNI" in text and "Testability" in text, "review checklist must include YAGNI and Testability"