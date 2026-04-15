from pathlib import Path

SKILL_FILE = Path(__file__).parents[2] / "skills" / "plan-review" / "SKILL.md"


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

    def test_file_map_heuristic_present(self):
        text = SKILL_FILE.read_text()
        assert (
            "file → tasks" in text or "file→tasks" in text
            or "file → [task" in text or "file-map" in text.lower()
        ), "Step 10 must describe the file-map heuristic"

    def test_pair_check_removed(self):
        text = SKILL_FILE.read_text()
        assert "for each pair" not in text.lower(), \
            "Step 10 must not instruct pair-wise checking"

    def test_step10_map_build_before_flag(self):
        text = SKILL_FILE.read_text()
        step10_idx = text.find("**Dependency hints**")
        assert step10_idx != -1, "Step 10 header must exist"
        step10_text = text[step10_idx:step10_idx + 600]
        map_mention = (
            "file→tasks" in step10_text or "file → tasks" in step10_text
            or "file → [task" in step10_text
        )
        flag_mention = "blocking" in step10_text
        assert map_mention, "Step 10 must describe building a file→tasks map"
        assert flag_mention, "Step 10 must describe flagging conflicts as blocking"
