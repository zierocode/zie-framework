"""Structural tests: /implement must document the resume-subagent pattern."""
import os
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMPLEMENT_CMD = Path(REPO_ROOT) / "commands" / "implement.md"


class TestImplementResumePattern:
    def _src(self):
        return IMPLEMENT_CMD.read_text()

    def test_subagent_usage_documented(self):
        """zie-implement.md must document async agent/subagent usage."""
        assert "agent" in self._src().lower(), (
            "zie-implement.md must mention agent usage"
        )

    def test_failure_recovery_documented(self):
        src = self._src()
        t = src.lower()
        assert "interrupt" in t or "surface" in t or "stuck" in t or "ask" in t, (
            "zie-implement.md must document what to do when implementation fails"
        )
