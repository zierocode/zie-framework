"""Structural tests: self-tuning proposals in retro.md must be non-blocking."""
from pathlib import Path

RETRO = Path(__file__).parents[2] / "commands" / "retro.md"


def _text() -> str:
    return RETRO.read_text()


class TestSelfTuningNonBlocking:
    def test_no_blocking_user_input_prompt(self):
        """Self-tuning must not block on 'apply' user input."""
        text = _text()
        assert 'Type "apply"' not in text and "Wait for user input" not in text, \
            "retro.md self-tuning must not wait for user input (blocking)"

    def test_self_tuning_runs_last(self):
        """Self-tuning section must appear after Suggest next."""
        text = _text()
        suggest_idx = text.find("Suggest next")
        tuning_idx = text.find("Self-tuning proposals\n\nNon-blocking")
        assert suggest_idx != -1, "retro.md must have 'Suggest next' section"
        assert tuning_idx != -1, "retro.md must have non-blocking self-tuning section"
        assert tuning_idx > suggest_idx, \
            "Self-tuning proposals must appear after Suggest next (non-blocking, last step)"

    def test_self_tuning_advisory_only(self):
        """Self-tuning output must direct user to /chore, not auto-apply."""
        text = _text()
        assert "/chore" in text, \
            "self-tuning must suggest /chore to apply proposals (not auto-apply)"

    def test_self_tuning_opt_out_config(self):
        """retro.md must support self_tuning_enabled: false opt-out."""
        text = _text()
        assert "self_tuning_enabled" in text, \
            "retro.md must check self_tuning_enabled key in .config"

    def test_self_tuning_commits_already_done(self):
        """Auto-commit section must appear before self-tuning proposals."""
        text = _text()
        commit_idx = text.find("Auto-commit retro outputs")
        tuning_idx = text.find("Self-tuning proposals\n\nNon-blocking")
        assert commit_idx != -1, "retro.md must have 'Auto-commit retro outputs'"
        assert tuning_idx != -1, "retro.md must have non-blocking self-tuning"
        assert commit_idx < tuning_idx, \
            "Auto-commit must complete before self-tuning proposals (non-blocking)"
