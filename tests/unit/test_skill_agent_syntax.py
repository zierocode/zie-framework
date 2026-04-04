"""Structural guard: no SKILL.md file may use @agent- syntax.
Skills must invoke reviewers via Skill() directly.
@agent- syntax is reserved for commands/ that spawn subagent worktrees.
"""
from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"


class TestNoAgentSyntaxInSkills:
    def test_no_agent_syntax_in_skills(self):
        skill_files = list(SKILLS_DIR.glob("*/SKILL.md"))
        assert skill_files, "No SKILL.md files found — check SKILLS_DIR path"
        violations = []
        for skill_file in skill_files:
            text = skill_file.read_text()
            if "@agent-" in text:
                for lineno, line in enumerate(text.splitlines(), 1):
                    if "@agent-" in line:
                        violations.append(f"{skill_file.name} (line {lineno}): {line.strip()}")
        assert not violations, (
            "Skills must not use @agent- syntax. "
            "Use Skill(zie-framework:<name>) instead.\n"
            + "\n".join(violations)
        )
