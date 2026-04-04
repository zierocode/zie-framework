"""Structural tests: /implement step 0 must show advisory (non-blocking) for non-agent mode."""
import os
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMPLEMENT_CMD = Path(REPO_ROOT) / "commands" / "implement.md"


class TestAgentModeConfirm:
    def _src(self):
        return IMPLEMENT_CMD.read_text()

    def test_no_blocking_interactive_confirmation(self):
        """Step 0 must NOT block with 'Continue anyway?' — advisory only."""
        src = self._src()
        assert "Continue anyway?" not in src, (
            "zie-implement.md step 0 must be advisory (non-blocking), not ask 'Continue anyway?'"
        )

    def test_step0_is_advisory(self):
        """Step 0 must say it is advisory and non-blocking."""
        src = self._src()
        assert "advisory" in src.lower() or "Tip" in src, (
            "zie-implement.md step 0 must be labeled as advisory"
        )

    def test_agent_mode_command_referenced(self):
        """Recommended agent mode command is documented."""
        src = self._src()
        assert "zie-implement-mode" in src, (
            "zie-implement.md step 0 must mention the recommended agent mode"
        )
