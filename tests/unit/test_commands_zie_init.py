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

    def test_pipeline_summary_after_print_summary_step(self):
        """Pipeline block must appear within or after the Print summary step."""
        content = read_init()
        print_summary_idx = content.find("**Print summary**")
        pipeline_idx = content.find("SDLC pipeline:")
        assert print_summary_idx != -1, "Print summary step not found in zie-init.md"
        assert pipeline_idx != -1, "SDLC pipeline block not found"
        assert pipeline_idx > print_summary_idx, (
            "Pipeline summary must appear after Print summary header"
        )

    def test_migration_complete_line_documented(self):
        """Migration complete line must be documented in Step 13."""
        content = read_init()
        assert "Migration complete:" in content
