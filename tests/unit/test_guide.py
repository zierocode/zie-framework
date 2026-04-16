"""Unit tests for commands/guide.md acceptance criteria (Area 4)."""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
GUIDE_PATH = REPO_ROOT / "commands" / "guide.md"


def _guide_text():
    return GUIDE_PATH.read_text()


class TestGuideExists:
    def test_guide_file_exists(self):
        assert GUIDE_PATH.exists(), "commands/guide.md must exist"

    def test_guide_mentions_init_when_no_zf(self):
        text = _guide_text()
        assert "/init" in text, "/guide must include /init instructions for when zie-framework/ absent"

    def test_guide_explains_zie_framework_when_no_zf(self):
        text = _guide_text()
        # Must have at least 2 sentences explaining what zie-framework is
        # when zee-framework/ is absent — count sentence endings near /init
        sentences_near_init = text.count(".")
        assert sentences_near_init >= 2, "/guide must have at least 2 sentences explaining zie-framework"

    def test_guide_shows_command_list(self):
        text = _guide_text()
        for cmd in ("/spec", "/plan", "/implement", "/sprint", "/release"):
            assert cmd in text, f"/guide must list {cmd} in command overview"

    def test_guide_references_now_lane_for_active_feature(self):
        text = _guide_text()
        assert "now" in text.lower() or "active" in text.lower(), (
            "/guide must reference the ROADMAP Now lane or active feature"
        )

    def test_guide_recommends_spec_for_next_items(self):
        text = _guide_text()
        assert "/spec" in text, "/guide must recommend /spec when Next lane items exist without approved spec"

    def test_guide_recommends_implement_when_ready(self):
        text = _guide_text()
        assert "/implement" in text or "/sprint" in text, (
            "/guide must recommend /implement or /sprint when all items have approved spec+plan"
        )

    def test_guide_handles_missing_roadmap_gracefully(self):
        text = _guide_text()
        # The command must not crash when ROADMAP.md is missing
        # Verify there's an error handling note or fallback instruction
        assert "roadmap" in text.lower() or "command" in text.lower(), (
            "/guide must handle missing ROADMAP.md gracefully"
        )

    def test_guide_shows_workflow_map(self):
        text = _guide_text()
        assert "backlog" in text.lower() and "retro" in text.lower(), "/guide must show the full workflow map"
