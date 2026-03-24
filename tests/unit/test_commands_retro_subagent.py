"""Structural tests: /zie-retro must reference the subagent-log."""
import os
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RETRO_CMD = Path(REPO_ROOT) / "commands" / "zie-retro.md"


class TestRetroSubagentSection:
    def _src(self):
        return RETRO_CMD.read_text()

    def test_retro_references_subagent_log(self):
        assert "subagent-log" in self._src(), (
            "zie-retro.md must reference 'subagent-log' to read the JSONL log"
        )

    def test_retro_has_subagent_activity_heading(self):
        src = self._src()
        assert "Subagent Activity" in src, (
            "zie-retro.md must contain a 'Subagent Activity' section heading"
        )

    def test_retro_handles_missing_log_gracefully(self):
        src = self._src()
        assert "No subagent activity" in src, (
            "zie-retro.md must document the 'No subagent activity' fallback message"
        )
