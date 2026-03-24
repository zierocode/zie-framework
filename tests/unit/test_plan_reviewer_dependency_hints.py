from pathlib import Path

SKILL_FILE = Path(__file__).parents[2] / "skills" / "plan-reviewer" / "SKILL.md"


class TestPlanReviewerDependencyHints:
    def test_skill_file_exists(self):
        assert SKILL_FILE.exists()

    def test_dependency_scan_item_present(self):
        text = SKILL_FILE.read_text()
        assert "**Dependency hints**" in text, \
            "Phase 2 must contain a Dependency hints item"

    def test_suggestion_output_format_exact(self):
        text = SKILL_FILE.read_text()
        assert (
            "Tasks N and M appear independent — consider adding "
            "`<!-- depends_on: -->` to enable parallel execution"
        ) in text, \
            "Suggestion output format does not match required exact text"

    def test_item_is_advisory_not_blocking(self):
        text = SKILL_FILE.read_text()
        assert "suggestion" in text.lower(), \
            "Dependency hints item must be labelled as a suggestion (not an error)"

    def test_existing_items_intact(self):
        text = SKILL_FILE.read_text()
        assert "**Header**" in text
        assert "**TDD structure**" in text
        assert "**YAGNI**" in text
