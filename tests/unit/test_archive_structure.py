"""Tests for archive directory structure, Makefile target, and zie-release.md reference."""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
ZF = REPO_ROOT / "zie-framework"
MAKEFILE = REPO_ROOT / "Makefile"
RELEASE_CMD = REPO_ROOT / "commands" / "release.md"


def test_archive_dirs_exist():
    """Archive subdirectories must exist."""
    assert (ZF / "archive" / "backlog").exists(), "archive/backlog/ missing"
    assert (ZF / "archive" / "specs").exists(), "archive/specs/ missing"
    assert (ZF / "archive" / "plans").exists(), "archive/plans/ missing"


def test_makefile_has_archive_target():
    """Makefile must have an 'archive' target."""
    text = MAKEFILE.read_text()
    assert "archive:" in text or "archive :" in text, "Makefile must define an 'archive' target"


def test_release_md_references_archive():
    """zie-release.md must reference the archive step after merge."""
    text = RELEASE_CMD.read_text()
    assert "archive" in text.lower(), "zie-release.md must reference archive step"
    assert "make archive" in text, "zie-release.md must include 'make archive' command"
