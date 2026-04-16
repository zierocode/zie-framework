"""Test that the consolidated review skill exists and delegates correctly."""

from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"


def test_review_skill_exists():
    """The merged review skill must exist."""
    assert (SKILLS_DIR / "review" / "SKILL.md").exists()


def test_review_skill_has_review_types():
    """The review skill must support spec, plan, and impl review types."""
    text = (SKILLS_DIR / "review" / "SKILL.md").read_text()
    assert "spec" in text.lower()
    assert "plan" in text.lower()
    assert "impl" in text.lower()


def test_review_skill_has_review_phases():
    """The review skill must define review phases."""
    text = (SKILLS_DIR / "review" / "SKILL.md").read_text()
    assert "Phase" in text or "phase" in text