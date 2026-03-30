"""Tests for context-lean-sprint Task 4: zie-plan passes context_bundle with adr_cache_path."""
from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "zie-plan.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestZiePlanContextBundle:
    def test_context_bundle_section_present(self):
        """zie-plan has context bundle loading section."""
        text = cmd_text()
        assert "context_bundle" in text and "context-load" in text, \
            "zie-plan must have context bundle loading section"

    def test_adr_cache_path_in_bundle(self):
        """context_bundle includes adr_cache_path."""
        text = cmd_text()
        assert "adr_cache_path" in text, \
            "zie-plan context_bundle must include adr_cache_path"

    def test_write_adr_cache_called(self):
        """write_adr_cache is called to build the cache."""
        text = cmd_text()
        assert "write_adr_cache" in text, \
            "zie-plan must call write_adr_cache"

    def test_bundle_passed_to_reviewer(self):
        """context_bundle is passed to plan-reviewer."""
        text = cmd_text()
        assert "context_bundle" in text and ("plan-reviewer" in text or "reviewer" in text.lower()), \
            "zie-plan must pass context_bundle to plan-reviewer"

    def test_single_load_comment(self):
        """Context loaded once per session (not per-slug)."""
        text = cmd_text()
        assert "once" in text.lower() or "session" in text.lower(), \
            "zie-plan must load context once per session"
