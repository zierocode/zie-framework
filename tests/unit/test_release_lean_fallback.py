"""Structural tests: zie-release.md must use graceful skip, not blocking fallback."""

from pathlib import Path

ROOT = Path(__file__).parents[2]
RELEASE_MD = ROOT / "commands" / "release.md"


class TestReleaseLeanFallback:
    def _release(self) -> str:
        return RELEASE_MD.read_text()

    def test_blocking_fallback_comment_removed(self):
        """Old blocking fallback comment must be replaced — it instructs calling Skill inline."""
        src = self._release()
        assert "call Skill(zie-framework:docs-sync) inline" not in src, (
            "Blocking fallback comment still present in zie-release.md — must be replaced"
        )

    def test_skip_message_present(self):
        """Release fallback must print a skip message, not block."""
        src = self._release()
        assert "docs-sync unavailable" in src, "zie-release.md fallback must print 'docs-sync unavailable' skip message"

    def test_manual_check_reference_present(self):
        """Release fallback must reference make docs-sync for manual check."""
        src = self._release()
        assert "make docs-sync" in src, "zie-release.md must reference 'make docs-sync' as the manual fallback"


class TestMakefileDocsSyncTarget:
    def _makefile(self) -> str:
        return (Path(__file__).parents[2] / "Makefile").read_text()

    def test_makefile_has_docs_sync_target(self):
        """Makefile must define a docs-sync target."""
        assert "docs-sync:" in self._makefile(), (
            "Makefile missing 'docs-sync:' target — needed as manual docs-sync path"
        )
