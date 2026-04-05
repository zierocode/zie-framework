from pathlib import Path

CMD = Path(__file__).parents[2] / "commands" / "implement.md"


def text():
    return CMD.read_text()


class TestInlineImplReviewer:
    def test_inline_review_present(self):
        assert "inline review" in text().lower() or "inline impl-review" in text().lower(), \
            "implement.md must describe inline review for HIGH-risk tasks"

    def test_no_background_agent_spawn(self):
        assert "@agent-impl-reviewer" not in text(), \
            "implement.md must not spawn @agent-impl-reviewer background agent"

    def test_auto_fix_protocol_present(self):
        t = text().lower()
        assert "auto-fix" in t or ("fix" in t and "retry" in t), \
            "implement.md must describe auto-fix protocol after review issues"

    def test_interrupt_on_fix_failure(self):
        t = text().lower()
        assert "interrupt" in t or "surface" in t, \
            "implement.md must interrupt sprint when auto-fix fails"
