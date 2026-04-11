"""Tests for sprint state persistence (resume) contract in commands/sprint.md."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD = REPO_ROOT / "commands" / "sprint.md"


def _text():
    return CMD.read_text()


class TestSprintResumeCheck:
    def test_sprint_state_file_referenced(self):
        """sprint.md must reference .sprint-state for resume detection."""
        assert ".sprint-state" in _text(), (
            "sprint.md must reference zie-framework/.sprint-state for resume/checkpoint"
        )

    def test_resume_check_in_preflight(self):
        """Resume check must happen in pre-flight (before AUDIT phase)."""
        text = _text()
        resume_idx = text.find(".sprint-state")
        audit_idx = text.find("## Step 0: AUDIT")
        assert resume_idx < audit_idx, (
            "Sprint resume check must come before Step 0 AUDIT"
        )

    def test_resume_offers_yes_restart(self):
        """Resume prompt must offer yes/restart options."""
        text = _text()
        assert "Resume" in text or "resume" in text, "must mention resume option"
        assert "restart" in text.lower(), "must offer restart option"

    def test_sprint_state_has_phase_field(self):
        """State JSON schema must include a phase field."""
        text = _text()
        assert '"phase"' in text, "sprint-state JSON must contain phase field"

    def test_sprint_state_has_remaining_items(self):
        """State JSON schema must include remaining_items field."""
        text = _text()
        assert "remaining_items" in text, "sprint-state JSON must contain remaining_items"

    def test_sprint_state_has_completed_phases(self):
        """State JSON schema must include completed_phases field."""
        text = _text()
        assert "completed_phases" in text, "sprint-state JSON must contain completed_phases"


class TestSprintStateWrites:
    def test_state_written_after_phase1(self):
        """State file must be written after Phase 1 completes."""
        text = _text()
        phase1_idx = text.index("PHASE 1")
        phase2_idx = text.index("PHASE 2")
        phase1_section = text[phase1_idx:phase2_idx]
        assert ".sprint-state" in phase1_section, (
            "Sprint state must be written after Phase 1 completes"
        )

    def test_state_written_after_phase2(self):
        """State file must be written after Phase 2 completes."""
        text = _text()
        phase2_idx = text.index("PHASE 2")
        phase3_idx = text.index("PHASE 3")
        phase2_section = text[phase2_idx:phase3_idx]
        assert ".sprint-state" in phase2_section, (
            "Sprint state must be written after Phase 2 completes"
        )

    def test_state_written_after_phase3(self):
        """State file must be written after Phase 3 completes."""
        text = _text()
        phase3_idx = text.index("PHASE 3")
        phase4_idx = text.index("PHASE 4")
        phase3_section = text[phase3_idx:phase4_idx]
        assert ".sprint-state" in phase3_section, (
            "Sprint state must be written after Phase 3 completes"
        )


class TestSprintStateCleanup:
    def test_state_deleted_after_retro(self):
        """State file must be deleted after retro (Phase 4) completes."""
        text = _text()
        phase4_idx = text.index("PHASE 4")
        phase4_section = text[phase4_idx:]
        assert "Delete" in phase4_section or "delete" in phase4_section, (
            "Sprint state must be deleted after sprint completes (Phase 4 retro)"
        )
        # Must reference the state file in the deletion instruction
        assert ".sprint-state" in phase4_section, (
            "Phase 4 must reference .sprint-state in cleanup instruction"
        )

    def test_malformed_state_handled(self):
        """Resume check must handle malformed .sprint-state gracefully."""
        text = _text()
        assert "malformed" in text.lower() or "corrupt" in text.lower(), (
            "sprint.md must describe how to handle malformed .sprint-state"
        )
