"""Tests for zie-implement.md pre-flight guard requirements."""
from pathlib import Path

IMPLEMENT_MD = Path(__file__).parents[2] / "commands" / "implement.md"


def test_implement_no_knowledge_hash_bang():
    """implement.md must not invoke knowledge-hash.py (drift handled by session-resume)."""
    text = IMPLEMENT_MD.read_text()
    assert "knowledge-hash.py" not in text, (
        "implement.md must not run knowledge-hash.py — drift detection is handled by session-resume.py"
    )


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
    assert "/init" in text, (
        "zie-implement.md must reference /init when ROADMAP.md missing"
    )
