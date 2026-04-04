"""Tests for zie-framework skills advanced features:
$ARGUMENTS[N] indexed access, argument-hint frontmatter,
zie-audit skill + reference.md supporting file, SKILL.md size guard.

Spec: zie-framework/specs/2026-03-24-skills-advanced-features-design.md
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SKILLS = ROOT / "skills"


def read_skill(name):
    return (SKILLS / name / "SKILL.md").read_text()


class TestArgumentIndexedDocs:
    def test_spec_design_has_argument_hint_frontmatter(self):
        content = read_skill("spec-design")
        assert "argument-hint:" in content, \
            "spec-design/SKILL.md must have argument-hint: in frontmatter"

    def test_spec_design_documents_arguments_0_as_slug(self):
        content = read_skill("spec-design")
        assert "$ARGUMENTS[0]" in content, \
            "spec-design/SKILL.md must document $ARGUMENTS[0] as slug"

    def test_spec_design_documents_arguments_1_as_mode(self):
        content = read_skill("spec-design")
        assert "$ARGUMENTS[1]" in content, \
            "spec-design/SKILL.md must document $ARGUMENTS[1] as mode"

    def test_spec_design_documents_mode_values(self):
        content = read_skill("spec-design")
        assert "full" in content and "quick" in content, \
            "spec-design/SKILL.md must document full and quick mode values"

    def test_spec_design_documents_absent_arg_fallback(self):
        content = read_skill("spec-design")
        assert "absent" in content or "fallback" in content or "default" in content, \
            "spec-design/SKILL.md must document default behaviour when args are absent"

    def test_write_plan_has_argument_hint_frontmatter(self):
        content = read_skill("write-plan")
        assert "argument-hint:" in content, \
            "write-plan/SKILL.md must have argument-hint: in frontmatter"

    def test_write_plan_documents_arguments_0_as_slug(self):
        content = read_skill("write-plan")
        assert "$ARGUMENTS[0]" in content, \
            "write-plan/SKILL.md must document $ARGUMENTS[0] as slug"

    def test_write_plan_documents_arguments_1_as_flags(self):
        content = read_skill("write-plan")
        assert "$ARGUMENTS[1]" in content, \
            "write-plan/SKILL.md must document $ARGUMENTS[1] as optional flags"

    def test_write_plan_documents_absent_arg_fallback(self):
        content = read_skill("write-plan")
        assert "absent" in content or "fallback" in content or "default" in content, \
            "write-plan/SKILL.md must document default behaviour when args are absent"

    def test_spec_design_documents_completeness_check(self):
        content = read_skill("spec-design")
        assert "Completeness" in content or "fast path" in content.lower(), \
            "spec-design/SKILL.md must document the fast-path completeness check"

    def test_write_plan_does_not_invoke_plan_reviewer(self):
        content = read_skill("write-plan")
        assert "plan-reviewer" not in content, \
            "write-plan/SKILL.md must NOT reference the plan-reviewer loop (reviewer gate belongs in zie-plan.md)"


class TestArgumentHintFrontmatter:
    NO_ARG_SKILLS = [
        "spec-reviewer",
        "plan-reviewer",
        "impl-reviewer",
        "debug",
        "tdd-loop",
        "test-pyramid",
    ]

    def test_all_no_arg_skills_have_argument_hint(self):
        for skill in self.NO_ARG_SKILLS:
            content = read_skill(skill)
            assert "argument-hint:" in content, \
                f"skills/{skill}/SKILL.md must have argument-hint: in frontmatter"

    def test_no_arg_skills_hint_is_empty_string(self):
        """Skills with no user-facing args must set argument-hint to empty string,
        not leave it absent. This makes intent explicit."""
        for skill in self.NO_ARG_SKILLS:
            content = read_skill(skill)
            assert 'argument-hint: ""' in content \
                or "argument-hint: ''" in content \
                or "argument-hint:\n" in content, \
                f"skills/{skill}/SKILL.md argument-hint must be empty string (not absent)"

    def test_all_skills_have_argument_hint(self):
        """Every skill directory must have argument-hint: — including the two
        updated in Task 1."""
        all_skills = [d.name for d in SKILLS.iterdir() if (d / "SKILL.md").exists()]
        for skill in all_skills:
            content = read_skill(skill)
            assert "argument-hint:" in content, \
                f"skills/{skill}/SKILL.md must have argument-hint: in frontmatter"


class TestZieAuditSkill:
    SKILL_PATH = SKILLS / "zie-audit" / "SKILL.md"
    REF_PATH = SKILLS / "zie-audit" / "reference.md"

    def test_skill_file_exists(self):
        assert self.SKILL_PATH.exists(), \
            "skills/zie-audit/SKILL.md must exist"

    def test_reference_file_exists(self):
        assert self.REF_PATH.exists(), \
            "skills/zie-audit/reference.md must exist"

    def test_skill_under_500_lines(self):
        lines = self.SKILL_PATH.read_text().splitlines()
        assert len(lines) < 500, \
            f"skills/zie-audit/SKILL.md must be under 500 lines (got {len(lines)})"

    def test_skill_has_argument_hint(self):
        content = self.SKILL_PATH.read_text()
        assert "argument-hint:" in content, \
            "skills/zie-audit/SKILL.md must have argument-hint: in frontmatter"

    def test_skill_argument_hint_includes_focus(self):
        content = self.SKILL_PATH.read_text()
        assert "--focus" in content, \
            "skills/zie-audit/SKILL.md argument-hint must document --focus flag"

    def test_skill_covers_all_9_dimensions(self):
        content = self.SKILL_PATH.read_text()
        dimensions = [
            "Security", "Lean", "Quality", "Docs", "Architecture",
            "Performance", "Depend", "Developer", "Standards",
        ]
        for dim in dimensions:
            assert dim in content, \
                f"skills/zie-audit/SKILL.md must reference the {dim} dimension"

    def test_skill_reads_reference_md_via_skill_dir(self):
        content = self.SKILL_PATH.read_text()
        assert "CLAUDE_SKILL_DIR" in content, \
            "skills/zie-audit/SKILL.md must reference ${CLAUDE_SKILL_DIR}/reference.md"
        assert "reference.md" in content, \
            "skills/zie-audit/SKILL.md must explicitly read reference.md"

    def test_skill_has_graceful_skip_for_reference(self):
        content = self.SKILL_PATH.read_text()
        assert "graceful" in content.lower() or "not found" in content.lower() \
            or "skip" in content.lower(), \
            "skills/zie-audit/SKILL.md must document graceful skip if reference.md is missing"

    def test_reference_has_scoring_rubric(self):
        content = self.REF_PATH.read_text()
        assert "100" in content, \
            "reference.md must document the start-at-100 scoring system"
        assert "Critical" in content and "High" in content, \
            "reference.md must document Critical and High severity deductions"

    def test_reference_has_dimension_definitions(self):
        content = self.REF_PATH.read_text()
        dimensions = ["Security", "Lean", "Quality", "Docs", "Architecture"]
        for dim in dimensions:
            assert dim in content, \
                f"reference.md must define the {dim} dimension"

    def test_reference_has_query_template_section(self):
        content = self.REF_PATH.read_text()
        assert "query" in content.lower() or "queries" in content.lower(), \
            "reference.md must contain a query template library section"

    def test_zie_audit_command_has_phases(self):
        """commands/audit.md must have multi-phase structure."""
        cmd_path = ROOT / "commands" / "audit.md"
        content = cmd_path.read_text()
        assert "Phase 1" in content and "Phase 4" in content, \
            "commands/audit.md must have at least 4 phases"


class TestSkillFileSizeGuard:
    def test_no_skill_md_exceeds_500_lines(self):
        """Line-count guard: keeps SKILL.md files lean and forces extraction
        of large reference sections into supporting files."""
        oversized = []
        for skill_dir in SKILLS.iterdir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                lines = skill_file.read_text().splitlines()
                if len(lines) >= 500:
                    oversized.append(f"{skill_dir.name}/SKILL.md ({len(lines)} lines)")
        assert not oversized, \
            "These SKILL.md files exceed 500 lines — extract reference content: " \
            + ", ".join(oversized)


class TestSkillDirReferencePattern:
    def test_zie_audit_uses_claude_skill_dir(self):
        content = read_skill("zie-audit")
        assert "${CLAUDE_SKILL_DIR}" in content, \
            "skills/zie-audit/SKILL.md must use ${CLAUDE_SKILL_DIR} to reference supporting files"

    def test_zie_audit_reference_md_is_loaded_explicitly(self):
        """The skill must explicitly read reference.md — it is never auto-injected."""
        content = read_skill("zie-audit")
        assert "reference.md" in content, \
            "skills/zie-audit/SKILL.md must explicitly name reference.md in its steps"
