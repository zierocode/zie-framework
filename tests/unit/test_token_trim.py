"""Tests for token trim — command files must be under word-count thresholds."""

from pathlib import Path

COMMANDS = Path(__file__).parents[2] / "commands"


def _word_count(path: Path) -> int:
    return len(path.read_text().split())


def test_zie_implement_word_count():
    """zie-implement.md must be ≤1000 words (standardised limit — sprint7)."""
    assert _word_count(COMMANDS / "implement.md") <= 1000


def test_zie_release_word_count():
    """zie-release.md must be ≤1000 words (standardised limit — sprint7)."""
    assert _word_count(COMMANDS / "release.md") <= 1000


def test_zie_retro_word_count():
    """zie-retro.md must be ≤1200 words (raised from 1000 — roadmap-done-rotation adds inline step)."""
    assert _word_count(COMMANDS / "retro.md") <= 1200
