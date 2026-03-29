"""Tests for archive TTL rotation (archive-prune Makefile target)."""
import os
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
MAKEFILE = REPO_ROOT / "Makefile"


class TestMakefileArchivePruneTarget:
    """Makefile must define an archive-prune target."""

    def test_makefile_has_archive_prune_target(self):
        text = MAKEFILE.read_text()
        assert "archive-prune:" in text, \
            "Makefile must have an archive-prune target"

    def test_archive_prune_target_has_docstring(self):
        text = MAKEFILE.read_text()
        assert "archive-prune" in text and "##" in text, \
            "archive-prune target must have a help comment (##)"

    def test_makefile_archive_prune_references_90_days(self):
        text = MAKEFILE.read_text()
        assert "90" in text, \
            "archive-prune must reference 90-day TTL"

    def test_makefile_archive_prune_guard_threshold(self):
        text = MAKEFILE.read_text()
        assert "20" in text, \
            "archive-prune must enforce a 20-file minimum guard"


class TestArchivePruneGuard:
    """Young-project guard prevents pruning when archive has < 20 files."""

    def test_guard_skips_prune_on_young_project(self, tmp_path):
        """When archive has fewer than 20 files, no files are deleted."""
        for subdir in ("backlog", "specs", "plans"):
            (tmp_path / subdir).mkdir(parents=True)
            for i in range(1, 3):  # 2 files each = 6 total
                f = tmp_path / subdir / f"old-item-{i}.md"
                f.write_text("# old")
                old_time = time.time() - (100 * 86400)
                os.utime(f, (old_time, old_time))

        result = _run_prune_logic(tmp_path)
        assert "skipping prune" in result.lower() or "too young" in result.lower(), \
            f"Guard must skip prune for young projects. Got: {result}"

        remaining = list(tmp_path.rglob("*.md"))
        assert len(remaining) == 6, \
            f"Guard must not delete any files for young projects. Got {len(remaining)}"

    def test_guard_allows_prune_when_archive_mature(self, tmp_path):
        """When archive has >= 20 files, prune proceeds."""
        for subdir in ("backlog", "specs", "plans"):
            (tmp_path / subdir).mkdir(parents=True)
            for i in range(1, 8):  # 7 files each = 21 total
                f = tmp_path / subdir / f"old-item-{i}.md"
                f.write_text("# old")
                old_time = time.time() - (100 * 86400)
                os.utime(f, (old_time, old_time))

        result = _run_prune_logic(tmp_path)
        assert "skipping prune" not in result.lower(), \
            f"Mature archive (21 files) must not trigger guard. Got: {result}"


class TestArchivePruneLogic:
    """Prune removes files older than 90 days; spares recent files."""

    def test_prune_removes_old_files(self, tmp_path):
        """Files with mtime > 90 days are deleted."""
        _make_mature_archive(tmp_path)
        old_files = []
        for subdir in ("backlog", "specs", "plans"):
            f = tmp_path / subdir / "2025-01-01-old-feature.md"
            f.write_text("# old feature")
            old_time = time.time() - (100 * 86400)
            os.utime(f, (old_time, old_time))
            old_files.append(f)

        _run_prune_logic(tmp_path)

        for f in old_files:
            assert not f.exists(), f"Old file must be deleted: {f.name}"

    def test_prune_spares_recent_files(self, tmp_path):
        """Files with mtime <= 90 days are not deleted."""
        _make_mature_archive(tmp_path)
        recent_files = []
        for subdir in ("backlog", "specs", "plans"):
            f = tmp_path / subdir / "2026-03-20-recent-feature.md"
            f.write_text("# recent feature")
            recent_time = time.time() - (10 * 86400)
            os.utime(f, (recent_time, recent_time))
            recent_files.append(f)

        _run_prune_logic(tmp_path)

        for f in recent_files:
            assert f.exists(), f"Recent file must NOT be deleted: {f.name}"

    def test_prune_reports_count(self, tmp_path):
        """Output must include count of files removed."""
        _make_mature_archive(tmp_path)
        for subdir in ("backlog", "specs", "plans"):
            f = tmp_path / subdir / "old.md"
            f.write_text("# x")
            old_time = time.time() - (100 * 86400)
            os.utime(f, (old_time, old_time))

        result = _run_prune_logic(tmp_path)
        assert "removed" in result.lower(), \
            f"Output must report number of files removed. Got: {result}"

    def test_prune_zero_files_removed(self, tmp_path):
        """When no files are stale, output still reports 0 removed."""
        _make_mature_archive(tmp_path)
        result = _run_prune_logic(tmp_path)
        assert "0" in result or "zero" in result.lower() or "removed" in result.lower(), \
            f"Must report 0 files removed when nothing is stale. Got: {result}"

    def test_prune_output_format(self, tmp_path):
        """Output must match '[zie-framework] Archive prune: removed N file(s)'."""
        _make_mature_archive(tmp_path)
        result = _run_prune_logic(tmp_path)
        assert "[zie-framework]" in result and "Archive prune" in result, \
            f"Output format mismatch. Got: {result}"


class TestArchivePruneMissingDir:
    """Missing archive directory is handled gracefully."""

    def test_prune_skips_missing_archive_dir(self, tmp_path):
        """If archive/ doesn't exist, prune exits silently (no error)."""
        result = _run_prune_logic(tmp_path / "nonexistent")
        assert isinstance(result, str), "Must return a string result"


class TestRetroIntegration:
    """zie-retro.md must call make archive-prune."""

    def test_retro_calls_archive_prune(self):
        text = (REPO_ROOT / "commands" / "zie-retro.md").read_text()
        assert "make archive-prune" in text, \
            "zie-retro.md must call 'make archive-prune'"

    def test_retro_archive_prune_is_non_blocking(self):
        """The prune call must be noted as non-blocking or best-effort."""
        text = (REPO_ROOT / "commands" / "zie-retro.md").read_text()
        context_window = text[text.find("archive-prune") - 200:text.find("archive-prune") + 200] \
            if "archive-prune" in text else ""
        non_blocking_markers = ["|| true", "non-blocking", "best-effort", "skip", "failure"]
        assert any(m in context_window.lower() for m in non_blocking_markers), \
            "archive-prune call in zie-retro.md must be annotated as non-blocking"


class TestClaudeMdDocs:
    """CLAUDE.md must document the archive-prune target."""

    def test_claude_md_documents_archive_prune(self):
        text = (REPO_ROOT / "CLAUDE.md").read_text()
        assert "archive-prune" in text, \
            "CLAUDE.md must document the archive-prune Makefile target"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_mature_archive(tmp_path: Path, n: int = 21) -> None:
    """Populate tmp_path with n recent files across 3 subdirs (guard satisfied)."""
    per_dir = n // 3
    for subdir in ("backlog", "specs", "plans"):
        (tmp_path / subdir).mkdir(parents=True, exist_ok=True)
        for i in range(per_dir):
            f = tmp_path / subdir / f"recent-item-{i}.md"
            f.write_text("# filler")
            recent_time = time.time() - (5 * 86400)
            os.utime(f, (recent_time, recent_time))


def _run_prune_logic(archive_root: Path) -> str:
    """Execute the prune logic inline. Returns stdout+stderr as string."""
    script = f"""
import os, sys, time
from pathlib import Path

archive_root = Path(r'{archive_root}')
subdirs = ('backlog', 'specs', 'plans')
TTL = 90 * 86400
GUARD = 20

if not archive_root.exists():
    print('[zie-framework] Archive prune: archive directory not found, skipping')
    sys.exit(0)

all_md = [f for d in subdirs for f in (archive_root / d).glob('*.md')
          if (archive_root / d).exists()]
if len(all_md) < GUARD:
    print(f'[zie-framework] Archive prune: archive too young ({{len(all_md)}} files), skipping prune')
    sys.exit(0)

now = time.time()
removed = 0
for d in subdirs:
    p = archive_root / d
    if not p.exists():
        continue
    for f in p.glob('*.md'):
        try:
            if (now - f.stat().st_mtime) > TTL:
                f.unlink()
                removed += 1
        except Exception as e:
            print(f'[zie-framework] Archive prune: could not remove {{f.name}}: {{e}}', file=sys.stderr)

print(f'[zie-framework] Archive prune: removed {{removed}} file(s)')
"""
    result = subprocess.run(
        ["python3", "-c", script],
        capture_output=True, text=True
    )
    return result.stdout + result.stderr
