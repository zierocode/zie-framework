from pathlib import Path

SKILL = Path(__file__).parents[2] / "skills" / "spec-design" / "SKILL.md"


def text():
    return SKILL.read_text()


class TestSpecDesignAutonomousMode:
    def test_autonomous_mode_argument_documented(self):
        assert "autonomous" in text(), \
            "spec-design must document autonomous as a valid $ARGUMENTS[1] value"

    def test_skips_interactive_steps_in_autonomous(self):
        t = text().lower()
        assert "autonomous" in t and ("skip" in t or "direct" in t), \
            "autonomous mode must skip interactive steps"

    def test_auto_approve_in_autonomous(self):
        t = text().lower()
        assert "autonomous" in t and ("auto-approve" in t or "automatically" in t), \
            "autonomous mode must auto-approve without user gate"

    def test_inline_reviewer_call_in_autonomous(self):
        t = text().lower()
        assert "autonomous" in t and "inline" in t, \
            "autonomous mode must call spec-reviewer inline"

    def test_standalone_mode_unchanged(self):
        assert "full" in text() and "quick" in text(), \
            "full and quick modes must remain documented (standalone /spec unchanged)"
