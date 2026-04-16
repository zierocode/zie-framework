from pathlib import Path

RETRO_CMD = Path(__file__).parents[2] / "commands" / "retro.md"


def _text() -> str:
    return RETRO_CMD.read_text()


class TestRetroNextActiveLoop:
    def test_suggest_next_step_present(self):
        assert "Suggest next" in _text(), "zie-retro.md must contain a 'Suggest next' step"

    def test_zie_plan_prompt_present(self):
        assert "/plan" in _text(), "zie-retro.md must contain a '/plan' prompt in the Suggest next step"

    def test_empty_backlog_fallback_present(self):
        assert "/backlog" in _text(), "zie-retro.md must contain the empty-backlog fallback referencing /backlog"
