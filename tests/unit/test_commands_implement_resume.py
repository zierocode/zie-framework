"""Structural tests: /zie-implement must document the resume-subagent pattern."""
import os
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMPLEMENT_CMD = Path(REPO_ROOT) / "commands" / "zie-implement.md"


class TestImplementResumePattern:
    def _src(self):
        return IMPLEMENT_CMD.read_text()

    def test_subagent_usage_documented(self):
        """zie-implement.md must document async agent/subagent usage."""
        assert "agent" in self._src().lower(), (
            "zie-implement.md must mention agent usage"
        )

    def test_fresh_subagent_fallback_documented(self):
        src = self._src()
        assert "fresh" in src or "new subagent" in src or "start" in src, (
            "zie-implement.md must document what to do when session has ended"
        )
