"""Verify that all three reviewer skills contain the ADR-000-summary loading instruction."""
import pytest
from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"

REVIEWER_SKILLS = [
    SKILLS_DIR / "spec-reviewer" / "SKILL.md",
    SKILLS_DIR / "plan-reviewer" / "SKILL.md",
    SKILLS_DIR / "impl-reviewer" / "SKILL.md",
]


@pytest.mark.parametrize("skill_path", REVIEWER_SKILLS, ids=lambda p: p.parent.name)
def test_reviewer_loads_summary_file(skill_path):
    content = skill_path.read_text(encoding="utf-8")
    assert "ADR-000-summary.md" in content, (
        f"{skill_path.parent.name}/SKILL.md does not reference ADR-000-summary.md"
    )


@pytest.mark.parametrize("skill_path", REVIEWER_SKILLS, ids=lambda p: p.parent.name)
def test_reviewer_retains_fallback_path(skill_path):
    content = skill_path.read_text(encoding="utf-8")
    assert "decisions/ADR-*.md" in content or "decisions/*.md" in content, (
        f"{skill_path.parent.name}/SKILL.md lost the fallback ADR glob pattern"
    )
