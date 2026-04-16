from pathlib import Path

SKILL_PATH = Path(__file__).parents[2] / "skills" / "spec-design" / "SKILL.md"


def skill_text() -> str:
    return SKILL_PATH.read_text()


class TestBatchApprovalStructure:
    def test_skill_file_exists(self):
        assert SKILL_PATH.exists()

    def test_section_by_section_approval_removed(self):
        assert "get approval after each" not in skill_text(), "section-by-section approval phrase must be removed"

    def test_single_review_prompt_present(self):
        assert "Does this look right" in skill_text(), "single full-draft review prompt must be present"

    def test_batch_edit_language_present(self):
        assert "apply all in one batch" in skill_text(), "batch edit language must be present"

    def test_all_sections_still_present(self):
        text = skill_text()
        for section in (
            "Problem & Motivation",
            "Architecture & Components",
            "Data Flow",
            "Edge Cases",
            "Out of Scope",
        ):
            assert section in text, f"section must remain: {section}"

    def test_review_invocation_still_present(self):
        assert "review" in skill_text(), "review invocation must remain intact"