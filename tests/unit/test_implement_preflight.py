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


def test_implement_has_wip1_guard():
    """zie-implement.md must check Now lane and stop if already occupied (WIP=1)."""
    text = IMPLEMENT_MD.read_text()
    assert "WIP=1" in text, (
        "zie-implement.md must have a WIP=1 guard section"
    )
    assert "Now lane" in text or "Now" in text, (
        "zie-implement.md WIP=1 guard must reference the Now lane"
    )


def test_implement_wip1_stop_message():
    """WIP=1 guard STOP message must name the active task."""
    text = IMPLEMENT_MD.read_text()
    assert "WIP=1 active" in text, (
        "WIP=1 STOP message must include 'WIP=1 active' to name the blocking task"
    )
    assert "Finish or release" in text, (
        "WIP=1 STOP message must instruct user to finish or release before starting new work"
    )


def test_implement_wip1_guard_before_pull():
    """WIP=1 guard (step 2) must appear before 'Pull first Ready item' (step 3)."""
    text = IMPLEMENT_MD.read_text()
    wip_pos = text.find("WIP=1 guard")
    pull_pos = text.find("Pull first Ready item")
    assert wip_pos != -1, "WIP=1 guard section missing"
    assert pull_pos != -1, "'Pull first Ready item' step missing"
    assert wip_pos < pull_pos, "WIP=1 guard must precede the 'Pull first Ready item' step"
