from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"
SKILLS_DIR = Path(__file__).parents[2] / "skills"


class TestZiePlanContextLoad:
    def test_context_load_marker_present(self):
        text = (COMMANDS_DIR / "plan.md").read_text()
        assert "<!-- context-load: adrs + project context -->" in text, (
            "zie-plan.md must have context-load comment marker"
        )

    def test_adrs_load_step_present(self):
        text = (COMMANDS_DIR / "plan.md").read_text()
        assert "decisions/" in text, "zie-plan.md must load zie-framework/decisions/*.md"

    def test_context_md_load_step_present(self):
        text = (COMMANDS_DIR / "plan.md").read_text()
        assert "project/context.md" in text, "zie-plan.md must load zie-framework/project/context.md"

    def test_reviewer_invocation_passes_bundle(self):
        text = (COMMANDS_DIR / "plan.md").read_text()
        assert "context_bundle" in text, "zie-plan.md must pass context_bundle to reviewer invocation"


class TestZieImplementContextLoad:
    def test_context_load_marker_present(self):
        text = (COMMANDS_DIR / "implement.md").read_text()
        assert "<!-- context-load: adrs + project context -->" in text, (
            "zie-implement.md must have context-load comment marker"
        )

    def test_adrs_load_step_present(self):
        text = (COMMANDS_DIR / "implement.md").read_text()
        assert "decisions/" in text, "zie-implement.md must load zie-framework/decisions/*.md"

    def test_context_md_load_step_present(self):
        text = (COMMANDS_DIR / "implement.md").read_text()
        assert "project/context.md" in text, "zie-implement.md must load zie-framework/project/context.md"

    def test_reviewer_invocation_passes_bundle(self):
        text = (COMMANDS_DIR / "implement.md").read_text()
        assert "context_bundle" in text, "zie-implement.md must pass context_bundle to reviewer invocation"


class TestSpecReviewerContextBundle:
    def test_context_bundle_required(self):
        text = (SKILLS_DIR / "spec-review" / "SKILL.md").read_text()
        assert "context_bundle" in text, "spec-review SKILL.md must reference context_bundle"

    def test_phase1_validation_present(self):
        text = (SKILLS_DIR / "spec-review" / "SKILL.md").read_text()
        assert "Phase 1" in text and "Validate Context Bundle" in text, (
            "spec-review SKILL.md must have Phase 1 bundle validation"
        )

    def test_disk_fallback_documented(self):
        text = (SKILLS_DIR / "spec-review" / "SKILL.md").read_text()
        # Must document fallback when bundle unavailable
        assert "disk" in text.lower() or "fallback" in text.lower() or "decisions/" in text, (
            "spec-review SKILL.md must document disk fallback"
        )


class TestPlanReviewerContextBundle:
    def test_context_bundle_required(self):
        text = (SKILLS_DIR / "plan-review" / "SKILL.md").read_text()
        assert "context_bundle" in text, "plan-review SKILL.md must reference context_bundle"

    def test_phase1_validation_present(self):
        text = (SKILLS_DIR / "plan-review" / "SKILL.md").read_text()
        assert "Phase 1" in text and "Validate Context Bundle" in text, (
            "plan-review SKILL.md must have Phase 1 bundle validation"
        )

    def test_disk_fallback_documented(self):
        text = (SKILLS_DIR / "plan-review" / "SKILL.md").read_text()
        assert "disk" in text.lower() or "fallback" in text.lower() or "decisions/" in text, (
            "plan-review SKILL.md must document disk fallback"
        )


class TestImplReviewerContextBundle:
    def test_context_bundle_required(self):
        text = (SKILLS_DIR / "impl-review" / "SKILL.md").read_text()
        assert "context_bundle" in text, "impl-review SKILL.md must reference context_bundle"

    def test_phase1_validation_present(self):
        text = (SKILLS_DIR / "impl-review" / "SKILL.md").read_text()
        assert "Phase 1" in text and "Validate Context Bundle" in text, (
            "impl-review SKILL.md must have Phase 1 bundle validation"
        )

    def test_modified_files_step_intact(self):
        text = (SKILLS_DIR / "impl-review" / "SKILL.md").read_text()
        assert "files changed" in text or "files changed" in text.lower(), (
            "impl-review SKILL.md must reference caller's files changed list"
        )
