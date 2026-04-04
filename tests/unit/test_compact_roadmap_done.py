"""Unit tests for hooks/utils.py::compact_roadmap_done."""
import sys
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "hooks"))

from utils_roadmap import compact_roadmap_done


def _date_str(months_ago: int) -> str:
    today = date.today()
    d = today - timedelta(days=months_ago * 30)
    return d.strftime("%Y-%m-%d")


def _make_roadmap(tmp_path: Path, done_entries: list) -> Path:
    lines = ["# ROADMAP\n", "\n", "## Done\n", "\n"]
    for entry in done_entries:
        lines.append(entry + "\n")
    lines += ["\n", "## Icebox\n"]
    p = tmp_path / "ROADMAP.md"
    p.write_text("".join(lines))
    return p


class TestNoCompaction:
    def test_count_exactly_20_no_compaction(self, tmp_path):
        entries = [f"- [x] feature-{i} — v1.{i}.0 {_date_str(8)}" for i in range(20)]
        p = _make_roadmap(tmp_path, entries)
        result = compact_roadmap_done(str(p))
        assert result == (False, 0, "")

    def test_count_below_20_no_compaction(self, tmp_path):
        entries = [f"- [x] feature-{i} — v1.{i}.0 {_date_str(8)}" for i in range(10)]
        p = _make_roadmap(tmp_path, entries)
        result = compact_roadmap_done(str(p))
        assert result == (False, 0, "")

    def test_count_above_20_but_all_recent_no_compaction(self, tmp_path):
        entries = [f"- [x] feature-{i} — v1.{i}.0 {_date_str(1)}" for i in range(21)]
        p = _make_roadmap(tmp_path, entries)
        result = compact_roadmap_done(str(p))
        assert result == (False, 0, "")

    def test_missing_file_no_compaction(self, tmp_path):
        result = compact_roadmap_done(str(tmp_path / "nonexistent.md"))
        assert result == (False, 0, "")


class TestCompactionTriggers:
    def test_21_entries_with_old_ones_triggers(self, tmp_path):
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(5)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(16)]
        p = _make_roadmap(tmp_path, old + recent)
        was_compacted, old_count, version_range = compact_roadmap_done(str(p))
        assert was_compacted is True
        assert old_count == 5
        assert version_range != ""

    def test_return_tuple_types(self, tmp_path):
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(5)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(16)]
        p = _make_roadmap(tmp_path, old + recent)
        result = compact_roadmap_done(str(p))
        assert isinstance(result[0], bool)
        assert isinstance(result[1], int)
        assert isinstance(result[2], str)


class TestArchiveFile:
    def test_archive_file_created(self, tmp_path):
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(5)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(16)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" + "\n".join(old + recent) + "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        archive_dir = zie_dir / "archive"
        assert archive_dir.exists()
        archive_files = list(archive_dir.glob("ROADMAP-*.md"))
        assert len(archive_files) == 1

    def test_archive_file_contains_old_entries(self, tmp_path):
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] special-old-feature — v1.0.0 {_date_str(8)}"]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(20)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" + "\n".join(old + recent) + "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        archive_files = list((zie_dir / "archive").glob("ROADMAP-*.md"))
        content = archive_files[0].read_text()
        assert "special-old-feature" in content


class TestRoadmapRewrite:
    def test_old_entries_replaced_with_summary_line(self, tmp_path):
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" + "\n".join(old + recent) + "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        content = roadmap.read_text()
        assert "[archive]" in content
        assert "old-0" not in content
        assert "old-1" not in content
        assert "old-2" not in content

    def test_recent_entries_preserved(self, tmp_path):
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] keep-this-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" + "\n".join(old + recent) + "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        content = roadmap.read_text()
        for i in range(18):
            assert f"keep-this-{i}" in content

    def test_summary_line_format(self, tmp_path):
        import re
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" + "\n".join(old + recent) + "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        content = roadmap.read_text()
        assert re.search(r"\[archive\].*features shipped.*see", content)

    def test_existing_archive_lines_preserved(self, tmp_path):
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        existing_archive = (
            "- [archive] v1.0–v1.2 (2025-01 to 2025-03): 10 features shipped"
            " — see zie-framework/archive/ROADMAP-v1.0-v1.2.md"
        )
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n"
            + existing_archive + "\n"
            + "\n".join(old + recent)
            + "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        content = roadmap.read_text()
        assert existing_archive in content


class TestEdgeCases:
    def test_malformed_date_entry_skipped_safely(self, tmp_path):
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        malformed = "- [x] mystery feature — v1.0.0 not-a-date"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n"
            + malformed + "\n"
            + "\n".join(old + recent)
            + "\n\n## Icebox\n"
        )
        result = compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_idempotent_second_call_noop(self, tmp_path):
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" + "\n".join(old + recent) + "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        result2 = compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        assert result2 == (False, 0, "")

    def test_accepts_path_object(self, tmp_path):
        entries = [f"- [x] feature-{i} — v1.{i}.0 {_date_str(1)}" for i in range(5)]
        p = _make_roadmap(tmp_path, entries)
        result = compact_roadmap_done(p)
        assert result == (False, 0, "")
