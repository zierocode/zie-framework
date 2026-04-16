"""Tests for dependency hints in the unified review skill."""

from pathlib import Path

SKILL_FILE = Path(__file__).parents[2] / "skills" / "review" / "SKILL.md"


class TestReviewDependencyHints:
    def test_skill_file_exists(self):
        assert SKILL_FILE.exists()

    def test_dependency_scan_item_present(self):
        text = SKILL_FILE.read_text()
        assert "depend" in text.lower(), "review must mention dependency hints"

    def test_phase_param_documented(self):
        text = SKILL_FILE.read_text()
        assert "phase" in text.lower(), "review must document phase parameter"