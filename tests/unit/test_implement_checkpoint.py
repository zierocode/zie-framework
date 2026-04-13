"""Tests for per-task checkpoint commit in implement.md."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD = REPO_ROOT / "commands" / "implement.md"


def _text():
    return CMD.read_text()


class TestPerTaskCheckpoint:
    """implement.md must commit after each task to prevent context-overflow data loss."""

    def test_per_task_commit_mentioned(self):
        """implement.md must mention per-task checkpoint commit."""
        assert "checkpoint commit" in _text(), (
            "implement.md must include per-task checkpoint commit to prevent data loss"
        )

    def test_commit_after_task_complete(self):
        """Checkpoint commit must happen after marking task complete."""
        text = _text()
        task_done_idx = text.find("TaskUpdate")
        checkpoint_idx = text.find("checkpoint commit")
        assert task_done_idx > 0, "must have TaskUpdate step"
        assert checkpoint_idx > task_done_idx, (
            "checkpoint commit must come after TaskUpdate (marking task complete)"
        )

    def test_commit_in_task_loop(self):
        """Per-task commit must be inside the Task Loop, not just at the end."""
        text = _text()
        task_loop_idx = text.find("### Task Loop")
        all_complete_idx = text.find("## When All Tasks Complete")
        checkpoint_idx = text.find("Per-task checkpoint commit")
        assert task_loop_idx > 0, "must have Task Loop section"
        assert all_complete_idx > task_loop_idx, "must have All Tasks Complete section"
        assert task_loop_idx < checkpoint_idx < all_complete_idx, (
            "per-task checkpoint commit must be inside Task Loop, before All Tasks Complete"
        )

    def test_commit_includes_task_number(self):
        """Commit message must include task number for traceability."""
        text = _text()
        checkpoint_section = text[text.find("Per-task checkpoint"):]
        # Find the commit message pattern - should reference T{N}
        assert "T{" in checkpoint_section or "T{N}" in checkpoint_section, (
            "per-task commit message must include task number (T{N})"
        )