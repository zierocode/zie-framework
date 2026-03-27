"""Tests for zie-implement.md pre-flight guard requirements."""
from pathlib import Path

IMPLEMENT_MD = Path(__file__).parents[2] / "commands" / "zie-implement.md"


def test_implement_has_ready_lane_guard():
    """zie-implement.md must check Ready lane and stop if empty."""
    text = IMPLEMENT_MD.read_text()
    assert "Ready" in text
    assert "empty" in text.lower() or "no approved plan" in text.lower(), (
        "zie-implement.md must handle empty Ready lane explicitly"
    )


def test_implement_has_missing_roadmap_guard():
    """zie-implement.md must handle missing ROADMAP.md gracefully."""
    text = IMPLEMENT_MD.read_text()
    assert "not found" in text.lower() or "missing" in text.lower(), (
        "zie-implement.md must handle missing ROADMAP.md"
    )
    assert "zie-init" in text, (
        "zie-implement.md must reference /zie-init when ROADMAP.md missing"
    )
