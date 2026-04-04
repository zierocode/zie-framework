"""Structural tests: /implement step 0 must warn-only, not block."""
import os
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMPLEMENT_CMD = Path(REPO_ROOT) / "commands" / "implement.md"


class TestAgentModeWarnOnly:
    def _src(self):
        return IMPLEMENT_CMD.read_text()

    def test_no_interactive_confirmation(self):
        """Step 0 must not ask for yes/cancel confirmation."""
        src = self._src()
        assert "Continue anyway?" not in src, (
            "zie-implement.md step 0 must not contain interactive confirmation"
        )
        assert "yes / cancel" not in src, (
            "zie-implement.md step 0 must not contain yes/cancel gate"
        )

    def test_warn_only_present(self):
        """Step 0 must emit a warning and continue immediately."""
        src = self._src()
        assert "continue immediately" in src or "continue" in src.lower(), (
            "zie-implement.md step 0 must document warn-and-continue behavior"
        )
        assert "zie-implement-mode" in src, (
            "zie-implement.md step 0 must mention the recommended agent mode"
        )
