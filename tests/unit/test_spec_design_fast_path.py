from pathlib import Path

SKILL_PATH = Path(__file__).parents[2] / "skills" / "spec-design" / "SKILL.md"


def skill_text() -> str:
    return SKILL_PATH.read_text()


class TestSpecDesignFastPath:
    def test_completeness_check_logic_present(self):
        text = skill_text()
        assert "completeness" in text.lower(), "SKILL.md must contain a completeness check"

    def test_substantive_definition_present(self):
        text = skill_text()
        assert "2 sentences" in text or "≥2 sentences" in text or "two sentences" in text.lower(), (
            "SKILL.md must define 'substantive' as ≥2 sentences"
        )

    def test_fast_path_branch_present(self):
        text = skill_text()
        assert "fast" in text.lower() or "fast-path" in text.lower() or "fast path" in text.lower(), (
            "SKILL.md must contain a fast-path branch"
        )

    def test_fast_path_skips_to_approach_proposal(self):
        text = skill_text()
        assert "approach" in text.lower(), "SKILL.md fast path must reference approach proposal"

    def test_fallback_to_questions_present(self):
        text = skill_text()
        assert "clarif" in text.lower(), "SKILL.md must retain reference to clarifying questions fallback"

    def test_fast_path_not_applied_without_backlog(self):
        text = skill_text()
        assert "backlog" in text.lower(), "SKILL.md completeness check must be scoped to backlog items"

    def test_argument_precedence_documented(self):
        text = skill_text()
        assert "quick" in text and "full" in text, (
            "SKILL.md must reference both 'quick' and 'full' modes in the completeness check block"
        )

    def test_existing_steps_intact(self):
        text = skill_text()
        for step_phrase in (
            "Understand the idea",
            "Propose 2-3 approaches",
            "Draft all design sections",
            "Write spec",
            "Spec reviewer loop",
            "Record approval",
            "Store spec approval",
            "Print handoff",
        ):
            assert step_phrase in text, f"SKILL.md must retain existing step: '{step_phrase}'"
