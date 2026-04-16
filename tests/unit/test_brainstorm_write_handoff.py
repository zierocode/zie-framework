"""Tests for brainstorming SKILL.md structure and handoff.md template (Area 0)."""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SKILL_PATH = REPO_ROOT / "skills" / "brainstorm" / "SKILL.md"


def _skill_text():
    return SKILL_PATH.read_text()


class TestBrainstormSkillExists:
    def test_skill_file_exists(self):
        assert SKILL_PATH.exists(), "Expected skills/brainstorm/SKILL.md to exist"

    def test_skill_has_four_phases(self):
        text = _skill_text()
        for phase in ("Phase 1", "Phase 2", "Phase 3", "Phase 4"):
            assert phase in text, f"SKILL.md must contain '{phase}'"

    def test_skill_references_handoff_md(self):
        text = _skill_text()
        assert "handoff.md" in text, "SKILL.md must reference .zie/handoff.md"

    def test_skill_references_brainstorm_active_flag(self):
        text = _skill_text()
        assert "brainstorm-active" in text, "SKILL.md must instruct writing brainstorm-active flag"

    def test_skill_references_zie_dir(self):
        text = _skill_text()
        assert ".zie/" in text, "SKILL.md must reference the .zie/ directory"


class TestHandoffMdTemplate:
    def test_handoff_has_goals_section(self):
        text = _skill_text()
        assert "## Goals" in text, "SKILL.md handoff template must include ## Goals"

    def test_handoff_has_key_decisions_section(self):
        text = _skill_text()
        assert "## Key Decisions" in text, "SKILL.md handoff template must include ## Key Decisions"

    def test_handoff_has_next_step_section(self):
        text = _skill_text()
        assert "## Next Step" in text, "SKILL.md must include ## Next Step in handoff template"

    def test_handoff_has_frontmatter_fields(self):
        text = _skill_text()
        assert "captured_at:" in text, "SKILL.md handoff template must have captured_at: field"
        assert "source: brainstorm" in text, "SKILL.md handoff template must set source: brainstorm"

    def test_skill_references_project_tmp_path_in_phase_4(self):
        text = _skill_text()
        # Must appear in the Phase 4 section, not just anywhere in the file
        phase4_idx = text.find("Phase 4")
        assert phase4_idx != -1, "SKILL.md must contain a Phase 4 section"
        phase4_text = text[phase4_idx:]
        assert "project_tmp_path" in phase4_text, (
            "SKILL.md Phase 4 must reference project_tmp_path for the brainstorm-active flag"
        )


class TestFreshnessCheckInSkill:
    def test_skill_references_resync_on_stale(self):
        text = _skill_text()
        assert "/resync" in text, "SKILL.md Phase 1 must mention /resync when PROJECT.md is stale"

    def test_skill_references_tech_stack_detection(self):
        text = _skill_text()
        # Should mention detecting the tech stack for scoping research
        assert any(term in text for term in ("tech stack", "package.json", "pyproject.toml")), (
            "SKILL.md must reference tech stack detection (package.json/pyproject.toml)"
        )
