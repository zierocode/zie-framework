"""Verify that all three reviewer skills use context_bundle for ADR loading."""

from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).parents[2] / "skills"

REVIEWER_SKILLS = [
    SKILLS_DIR / "spec-review" / "SKILL.md",
    SKILLS_DIR / "plan-review" / "SKILL.md",
    SKILLS_DIR / "impl-review" / "SKILL.md",
]


@pytest.mark.parametrize("skill_path", REVIEWER_SKILLS, ids=lambda p: p.parent.name)
def test_reviewer_uses_context_bundle(skill_path):
    """Reviewers receive ADRs via context_bundle from caller (not disk reads)."""
    content = skill_path.read_text(encoding="utf-8")
    assert "context_bundle" in content, f"{skill_path.parent.name}/SKILL.md does not reference context_bundle"
    # Verify Phase 1 validates context_bundle
    assert "Phase 1" in content and "Validate Context Bundle" in content, (
        f"{skill_path.parent.name}/SKILL.md missing Phase 1 context bundle validation"
    )


@pytest.mark.parametrize("skill_path", REVIEWER_SKILLS, ids=lambda p: p.parent.name)
def test_reviewer_has_disk_fallback_documented(skill_path):
    """Skills should document fallback behavior when context_bundle unavailable."""
    content = skill_path.read_text(encoding="utf-8")
    # Allow either explicit disk fallback OR clear statement that bundle is required
    has_bundle_requirement = "context_bundle required" in content.lower()
    has_disk_fallback = "decisions/" in content and ("ADR" in content or "disk" in content.lower())
    assert has_bundle_requirement or has_disk_fallback, (
        f"{skill_path.parent.name}/SKILL.md missing both bundle requirement and disk fallback"
    )
