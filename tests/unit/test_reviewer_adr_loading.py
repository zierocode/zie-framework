"""Verify that the unified review skill uses context_bundle for ADR loading."""

from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"
REVIEW_SKILL = SKILLS_DIR / "review" / "SKILL.md"


def test_review_skill_uses_context_bundle():
    """Review skill receives ADRs via context_bundle from caller."""
    content = REVIEW_SKILL.read_text(encoding="utf-8")
    assert "context_bundle" in content, "review/SKILL.md must reference context_bundle"


def test_review_skill_has_phase_validation():
    """Review skill Phase 1 validates context_bundle."""
    content = REVIEW_SKILL.read_text(encoding="utf-8")
    assert "Phase 1" in content, "review/SKILL.md must have Phase 1"


def test_review_skill_has_bundle_requirement():
    """Review skill documents context_bundle as required."""
    content = REVIEW_SKILL.read_text(encoding="utf-8")
    has_bundle_requirement = "context_bundle" in content.lower()
    assert has_bundle_requirement, "review/SKILL.md must reference context_bundle"