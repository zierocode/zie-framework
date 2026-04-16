"""Tests for Phase 2 resilience additions in commands/sprint.md."""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SPRINT_MD = REPO_ROOT / "commands" / "sprint.md"


def _phase2_loop_section(text: str) -> str:
    """Extract the Phase 2 per-item loop body (between loop start and phase end)."""
    loop_start = "For each Ready item"
    phase_end = "After all impl"
    start = text.index(loop_start)
    end = text.index(phase_end)
    return text[start:end]


def test_phase2_updates_state_per_item():
    """After each item, sprint must update .sprint-state with completion status."""
    text = SPRINT_MD.read_text()
    loop = _phase2_loop_section(text)
    assert ".sprint-state" in loop, "Phase 2 loop must update .sprint-state per item"


def test_phase2_resume_skips_completed():
    """Sprint resume with phase=2 must use remaining_items to skip completed slugs."""
    text = SPRINT_MD.read_text()
    assert "remaining_items" in text, "Resume logic must reference remaining_items to skip completed items"


def test_phase2_compact_between_items():
    """Sprint must run /compact between Phase 2 items and print confirmation."""
    text = SPRINT_MD.read_text()
    loop = _phase2_loop_section(text)
    assert "compact" in loop.lower(), "Phase 2 loop must include /compact between items"
    assert "context cleared" in loop, "Phase 2 loop must reference context cleared after item"
