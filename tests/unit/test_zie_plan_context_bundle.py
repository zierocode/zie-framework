"""Tests for context-lean-sprint Task 4: zie-plan passes context_bundle via skill invocation."""

from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "plan.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestZiePlanContextBundle:
    def test_context_bundle_section_present(self):
        """zie-plan has context bundle loading section."""
        text = cmd_text()
        assert "context_bundle" in text and "context-load" in text, "zie-plan must have context bundle loading section"

    def test_context_skill_invoked(self):
        """zie-plan invokes context skill to build bundle."""
        text = cmd_text()
        assert "Skill(zie-framework:context" in text, "zie-plan must invoke context skill"

    def test_bundle_passed_to_reviewer(self):
        """context_bundle is passed to reviewer."""
        text = cmd_text()
        assert "context_bundle" in text and ("review" in text.lower()), (
            "zie-plan must pass context_bundle to reviewer"
        )

    def test_single_load_comment(self):
        """Context loaded once per session (not per-slug)."""
        text = cmd_text()
        assert "once" in text.lower() or "session" in text.lower(), "zie-plan must load context once per session"
