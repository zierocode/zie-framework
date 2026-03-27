"""Tests for token trim — command files must be under word-count thresholds."""
from pathlib import Path

COMMANDS = Path(__file__).parents[2] / "commands"


def _word_count(path: Path) -> int:
    return len(path.read_text().split())


def test_zie_implement_word_count():
    """zie-implement.md must be ≤710 words (trimmed from 716; Task 11 pre-flight guard added)."""
    assert _word_count(COMMANDS / "zie-implement.md") <= 710


def test_zie_release_word_count():
    """zie-release.md must be ≤1047 words (≥10% trim from 1163)."""
    assert _word_count(COMMANDS / "zie-release.md") <= 1047


def test_zie_retro_word_count():
    """zie-retro.md must be ≤946 words (≥10% trim from 1051)."""
    assert _word_count(COMMANDS / "zie-retro.md") <= 946
