"""Tests for effort: frontmatter in skills and commands."""
from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"
ALLOWED_HIGH = {"spec-design"}  # only skill justified at high


def test_no_unexpected_high_effort_skills():
    """Only spec-design may have effort: high."""
    violations = []
    for skill_md in SKILLS_DIR.rglob("SKILL.md"):
        text = skill_md.read_text()
        for line in text.splitlines():
            if line.strip().startswith("effort:") and "high" in line:
                skill_name = skill_md.parent.name
                if skill_name not in ALLOWED_HIGH:
                    violations.append(f"{skill_md}: {line.strip()}")
    assert not violations, f"Unexpected high-effort skills: {violations}"
