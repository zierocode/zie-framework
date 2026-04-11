"""Tests for Sprint D: medium-effort-optimization — effort field audit."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
COMMANDS_DIR = REPO_ROOT / "commands"


def _effort(path: Path) -> str | None:
    """Extract 'effort: <value>' from a markdown frontmatter block."""
    for line in path.read_text().splitlines():
        if line.startswith("effort:"):
            return line.split(":", 1)[1].strip()
    return None


class TestSkillEffortFields:
    def test_brainstorm_effort_medium(self):
        """brainstorm skill must use effort: medium (not high)."""
        val = _effort(SKILLS_DIR / "brainstorm" / "SKILL.md")
        assert val == "medium", f"brainstorm effort should be medium, got {val!r}"

    def test_spec_design_effort_medium(self):
        """spec-design skill must use effort: medium (not high)."""
        val = _effort(SKILLS_DIR / "spec-design" / "SKILL.md")
        assert val == "medium", f"spec-design effort should be medium, got {val!r}"

    def test_no_skill_has_effort_high(self):
        """No skill except explicitly justified ones should declare effort: high."""
        high_skills = []
        for skill_file in SKILLS_DIR.rglob("SKILL.md"):
            if _effort(skill_file) == "high":
                high_skills.append(skill_file.parent.name)
        assert high_skills == [], (
            f"Skills with effort:high (should be medium or low): {high_skills}"
        )


class TestCommandEffortFields:
    def test_sprint_effort_high(self):
        """sprint.md may retain effort:high — it orchestrates the full SDLC pipeline."""
        val = _effort(COMMANDS_DIR / "sprint.md")
        assert val == "high", "sprint.md is expected to declare effort:high (full SDLC orchestrator)"

    def test_implement_effort_medium(self):
        """implement.md must use effort: medium."""
        val = _effort(COMMANDS_DIR / "implement.md")
        assert val == "medium", f"implement.md effort should be medium, got {val!r}"

    def test_spec_effort_medium(self):
        """spec.md must use effort: medium."""
        val = _effort(COMMANDS_DIR / "spec.md")
        assert val == "medium", f"spec.md effort should be medium, got {val!r}"


class TestEffortADRExists:
    def test_adr_effort_routing_exists(self):
        """ADR-063 documenting effort routing strategy must exist."""
        adrs = list((REPO_ROOT / "zie-framework" / "decisions").glob("ADR-063-*.md"))
        assert adrs, "ADR-063 (effort routing strategy) must exist in decisions/"

    def test_adr_effort_routing_has_routing_table(self):
        """Effort routing ADR must contain a routing table with low/medium/high."""
        adrs = list((REPO_ROOT / "zie-framework" / "decisions").glob("ADR-063-*.md"))
        if not adrs:
            pytest.skip("ADR-063 not found")
        content = adrs[0].read_text()
        assert "low" in content and "medium" in content and "high" in content, (
            "ADR-063 must document all three effort levels"
        )
