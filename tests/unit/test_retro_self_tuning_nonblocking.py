"""Structural tests: self-tuning proposals in retro.md must be non-blocking."""

from pathlib import Path

RETRO = Path(__file__).parents[2] / "commands" / "retro.md"


def _text() -> str:
    return RETRO.read_text()


class TestSelfTuningNonBlocking:
    def test_no_blocking_user_input_prompt(self):
        """Self-tuning must not block on 'apply' user input."""
        text = _text()
        assert 'Type "apply"' not in text and "Wait for user input" not in text, (
            "retro.md self-tuning must not wait for user input (blocking)"
        )

    def test_self_tuning_is_non_blocking_after_commits(self):
        """Self-tuning section must be marked as non-blocking (runs last, after commits)."""
        text = _text()
        assert "Non-blocking" in text, "retro.md must mark self-tuning as Non-blocking"
        # Verify self-tuning comes after auto-commit
        commit_idx = text.find("Auto-commit retro outputs")
        tuning_idx = text.find("Self-tuning proposals")
        assert commit_idx != -1, "retro.md must have Auto-commit section"
        assert tuning_idx != -1, "retro.md must have Self-tuning proposals section"
        assert commit_idx < tuning_idx, "Self-tuning must appear after Auto-commit (runs after commits)"

    def test_self_tuning_is_non_blocking(self):
        """Self-tuning output must be advisory/non-blocking, not auto-apply."""
        text = _text()
        assert "Non-blocking" in text, "self-tuning section must be marked as Non-blocking"

    def test_self_tuning_opt_out_config(self):
        """retro.md must support self_tuning_enabled: false opt-out."""
        text = _text()
        assert "self_tuning_enabled" in text, "retro.md must check self_tuning_enabled key in .config"

    def test_self_tuning_commits_already_done(self):
        """Auto-commit section must appear before self-tuning proposals."""
        text = _text()
        commit_idx = text.find("Auto-commit retro outputs")
        tuning_idx = text.find("Self-tuning proposals")
        assert commit_idx != -1, "retro.md must have 'Auto-commit retro outputs'"
        assert tuning_idx != -1, "retro.md must have Self-tuning proposals"
        assert commit_idx < tuning_idx, "Auto-commit must complete before self-tuning proposals (non-blocking)"
