"""Tests for the unified review skill's context_bundle handling."""

from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"
REVIEW_SKILL = SKILLS_DIR / "review" / "SKILL.md"


def read_review():
    return REVIEW_SKILL.read_text()


class TestReviewContextBundle:
    def test_context_bundle_required(self):
        assert "context_bundle" in read_review(), "review skill must reference context_bundle"

    def test_phase1_validation_present(self):
        text = read_review()
        assert "Phase 1" in text, "review must have Phase 1"
        assert "Validate Context Bundle" in text, "review Phase 1 must validate context_bundle"

    def test_disk_fallback_documented(self):
        text = read_review().lower()
        assert "disk" in text or "fallback" in text or "absent" in text, (
            "review must document fallback when bundle unavailable"
        )

    def test_phase_param_documented(self):
        text = read_review()
        assert "phase" in text.lower(), "review must document phase parameter"

    def test_spec_checklist_present(self):
        text = read_review()
        assert "spec" in text.lower(), "review must cover spec phase"

    def test_plan_checklist_present(self):
        text = read_review()
        assert "plan" in text.lower(), "review must cover plan phase"

    def test_impl_checklist_present(self):
        text = read_review()
        assert "impl" in text.lower(), "review must cover impl phase"

    def test_modified_files_step_intact(self):
        """impl phase must reference caller's files changed list or changed files."""
        text = read_review()
        assert "changed" in text.lower() or "files" in text.lower(), (
            "review must reference file changes for impl phase"
        )