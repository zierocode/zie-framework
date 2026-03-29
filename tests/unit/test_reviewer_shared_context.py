from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"
SKILLS_DIR   = Path(__file__).parents[2] / "skills"


class TestZiePlanContextLoad:
    def test_context_load_marker_present(self):
        text = (COMMANDS_DIR / "zie-plan.md").read_text()
        assert "<!-- context-load: adrs + project context -->" in text, \
            "zie-plan.md must have context-load comment marker"

    def test_adrs_load_step_present(self):
        text = (COMMANDS_DIR / "zie-plan.md").read_text()
        assert "decisions/" in text, \
            "zie-plan.md must load zie-framework/decisions/*.md"

    def test_context_md_load_step_present(self):
        text = (COMMANDS_DIR / "zie-plan.md").read_text()
        assert "project/context.md" in text, \
            "zie-plan.md must load zie-framework/project/context.md"

    def test_reviewer_invocation_passes_bundle(self):
        text = (COMMANDS_DIR / "zie-plan.md").read_text()
        assert "context_bundle" in text, \
            "zie-plan.md must pass context_bundle to reviewer invocation"


class TestZieImplementContextLoad:
    def test_context_load_marker_present(self):
        text = (COMMANDS_DIR / "zie-implement.md").read_text()
        assert "<!-- context-load: adrs + project context -->" in text, \
            "zie-implement.md must have context-load comment marker"

    def test_adrs_load_step_present(self):
        text = (COMMANDS_DIR / "zie-implement.md").read_text()
        assert "decisions/" in text, \
            "zie-implement.md must load zie-framework/decisions/*.md"

    def test_context_md_load_step_present(self):
        text = (COMMANDS_DIR / "zie-implement.md").read_text()
        assert "project/context.md" in text, \
            "zie-implement.md must load zie-framework/project/context.md"

    def test_reviewer_invocation_passes_bundle(self):
        text = (COMMANDS_DIR / "zie-implement.md").read_text()
        assert "context_bundle" in text, \
            "zie-implement.md must pass context_bundle to reviewer invocation"


class TestSpecReviewerFallback:
    def test_bundle_preamble_present(self):
        text = (SKILLS_DIR / "spec-reviewer" / "SKILL.md").read_text()
        assert "if context_bundle provided" in text, \
            "spec-reviewer SKILL.md Phase 1 must have bundle conditional preamble"

    def test_disk_fallback_mentioned(self):
        text = (SKILLS_DIR / "spec-reviewer" / "SKILL.md").read_text()
        assert "read from disk" in text, \
            "spec-reviewer SKILL.md must mention disk fallback path"

    def test_phase_1_steps_intact(self):
        text = (SKILLS_DIR / "spec-reviewer" / "SKILL.md").read_text()
        assert "decisions/" in text, \
            "spec-reviewer SKILL.md Phase 1 must still reference decisions/*.md"
        assert "project/context.md" in text, \
            "spec-reviewer SKILL.md Phase 1 must still reference project/context.md"


class TestPlanReviewerFallback:
    def test_bundle_preamble_present(self):
        text = (SKILLS_DIR / "plan-reviewer" / "SKILL.md").read_text()
        assert "if context_bundle provided" in text, \
            "plan-reviewer SKILL.md Phase 1 must have bundle conditional preamble"

    def test_disk_fallback_mentioned(self):
        text = (SKILLS_DIR / "plan-reviewer" / "SKILL.md").read_text()
        assert "read from disk" in text, \
            "plan-reviewer SKILL.md must mention disk fallback path"

    def test_phase_1_steps_intact(self):
        text = (SKILLS_DIR / "plan-reviewer" / "SKILL.md").read_text()
        assert "decisions/" in text, \
            "plan-reviewer SKILL.md Phase 1 must still reference decisions/*.md"
        assert "project/context.md" in text, \
            "plan-reviewer SKILL.md Phase 1 must still reference project/context.md"


class TestImplReviewerFallback:
    def test_bundle_preamble_present(self):
        text = (SKILLS_DIR / "impl-reviewer" / "SKILL.md").read_text()
        assert "if context_bundle provided" in text, \
            "impl-reviewer SKILL.md Phase 1 must have bundle conditional preamble"

    def test_disk_fallback_mentioned(self):
        text = (SKILLS_DIR / "impl-reviewer" / "SKILL.md").read_text()
        assert "read from disk" in text, \
            "impl-reviewer SKILL.md must mention disk fallback path"

    def test_modified_files_step_intact(self):
        text = (SKILLS_DIR / "impl-reviewer" / "SKILL.md").read_text()
        assert "files changed" in text, \
            "impl-reviewer SKILL.md must still reference caller's files changed list"

    def test_phase_1_adr_ref_intact(self):
        text = (SKILLS_DIR / "impl-reviewer" / "SKILL.md").read_text()
        assert "decisions/" in text, \
            "impl-reviewer SKILL.md Phase 1 must still reference decisions/*.md"
