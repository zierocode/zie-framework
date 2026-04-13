"""Tests for the conditional simplify step in commands/implement.md."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
IMPLEMENT_MD = REPO_ROOT / "commands" / "implement.md"


def test_simplify_step_present():
    text = IMPLEMENT_MD.read_text()
    assert "code-simplifier" in text
    assert "simplify" in text.lower()


def test_simplify_threshold_documented():
    text = IMPLEMENT_MD.read_text()
    assert "50" in text  # threshold


def test_simplify_is_conditional():
    text = IMPLEMENT_MD.read_text()
    assert "skipped" in text.lower()
