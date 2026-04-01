"""Tests for T10: Archive plans/ infrastructure."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


class TestMakefileArchivePlans:
    """Makefile must have an archive-plans target."""

    def test_makefile_has_archive_plans_target(self):
        makefile = (REPO_ROOT / "Makefile").read_text()
        assert "archive-plans" in makefile, \
            "Makefile must have an archive-plans target"

    def test_archive_plans_uses_plans_archive_dir(self):
        makefile = (REPO_ROOT / "Makefile").read_text()
        assert "plans/archive" in makefile, \
            "archive-plans target must reference plans/archive/"

    def test_archive_plans_moves_old_plans(self):
        makefile = (REPO_ROOT / "Makefile").read_text()
        # Must move files (mv or find + mv pattern)
        assert "mv " in makefile or "move" in makefile.lower(), \
            "archive-plans must move files to archive directory"


class TestKnowledgeHashSkipsArchive:
    """knowledge-hash.py must skip plans/archive/ directory."""

    def test_knowledge_hash_skips_plans_archive(self):
        content = (REPO_ROOT / "hooks" / "knowledge-hash.py").read_text()
        assert "archive" in content, \
            "knowledge-hash.py must skip plans/archive/ in hash computation"

    def test_knowledge_hash_archive_in_exclude(self):
        content = (REPO_ROOT / "hooks" / "knowledge-hash.py").read_text()
        # Either in EXCLUDE set or explicit path skip
        assert "plans/archive" in content or \
               ("archive" in content and "EXCLUDE" in content), \
            "knowledge-hash.py must exclude plans/archive from hash"


class TestZieResyncExcludesArchive:
    """zie-resync.md must exclude plans/archive/ from resync scope."""

    def test_resync_excludes_plans_archive(self):
        content = (REPO_ROOT / "commands" / "zie-resync.md").read_text()
        assert "plans/archive" in content, \
            "zie-resync.md must exclude plans/archive/ from resync scope"
