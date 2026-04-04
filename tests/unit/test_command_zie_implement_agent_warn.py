"""Structural tests: /implement step 0 must warn and ask for confirmation."""
import os
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMPLEMENT_CMD = Path(REPO_ROOT) / "commands" / "implement.md"


class TestAgentModeConfirm:
    def _src(self):
        return IMPLEMENT_CMD.read_text()

    def test_interactive_confirmation_present(self):
        """Step 0 must ask for confirmation before continuing outside agent session."""
        src = self._src()
        assert "Continue anyway?" in src, (
            "zie-implement.md step 0 must ask for confirmation when outside agent session"
        )

    def test_stop_on_no(self):
        """Step 0 must STOP if user declines."""
        src = self._src()
        assert "no" in src.lower() and "STOP" in src, (
            "zie-implement.md step 0 must STOP when user answers no"
        )

    def test_agent_mode_command_referenced(self):
        """Recommended agent mode command is documented."""
        src = self._src()
        assert "zie-implement-mode" in src, (
            "zie-implement.md step 0 must mention the recommended agent mode"
        )
