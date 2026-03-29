"""Tests for commands/zie-init.md content spec compliance."""
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ZIE_INIT_MD = os.path.join(REPO_ROOT, "commands", "zie-init.md")


def read_init():
    with open(ZIE_INIT_MD) as f:
        return f.read()


class TestZieInitPipelineSummary:
    def test_pipeline_summary_present(self):
        """Step 13 must contain the SDLC pipeline block."""
        content = read_init()
        assert "SDLC pipeline:" in content

    def test_pipeline_all_stages_listed(self):
        """Pipeline block must list all 6 SDLC stages in order."""
        content = read_init()
        stages = [
            "/zie-backlog", "/zie-spec", "/zie-plan",
            "/zie-implement", "/zie-release", "/zie-retro",
        ]
        for stage in stages:
            assert stage in content, f"Missing stage: {stage}"

    def test_pipeline_quality_gates_line(self):
        content = read_init()
        assert "Each stage enforces quality gates" in content

    def test_pipeline_first_feature_hint(self):
        content = read_init()
        assert 'First feature: /zie-backlog' in content

    def test_pipeline_summary_after_step_13(self):
        """Pipeline block must appear within or after the Step 13 section."""
        content = read_init()
        step13_idx = content.find("13. **Print summary**")
        pipeline_idx = content.find("SDLC pipeline:")
        assert step13_idx != -1, "Step 13 not found in zie-init.md"
        assert pipeline_idx != -1, "SDLC pipeline block not found"
        assert pipeline_idx > step13_idx, (
            "Pipeline summary must appear after Step 13 header"
        )

    def test_migration_complete_line_documented(self):
        """Migration complete line must be documented in Step 13."""
        content = read_init()
        assert "Migration complete:" in content
