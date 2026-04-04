"""Tests for parse_roadmap_items_with_dates() in utils_roadmap.py."""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
from utils_roadmap import parse_roadmap_items_with_dates


class TestParseRoadmapItemsWithDates:
    def test_returns_list_of_tuples(self, tmp_path):
        """Returns list of (text, date) tuples."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Next\n- [ ] old-feature — 2026-01-01\n- [ ] new-feature\n")
        result = parse_roadmap_items_with_dates(roadmap, "next")
        assert len(result) == 2
        texts = [r[0] for r in result]
        assert any("old-feature" in t for t in texts)
        assert any("new-feature" in t for t in texts)

    def test_parses_iso_date_from_item(self, tmp_path):
        """ISO date YYYY-MM-DD in item line is returned as datetime.date."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Next\n- [ ] stale-item — [backlog](backlog/stale-item.md) 2025-12-01\n")
        result = parse_roadmap_items_with_dates(roadmap, "next")
        assert result[0][1] == datetime.date(2025, 12, 1)

    def test_none_date_when_no_date_in_item(self, tmp_path):
        """date=None when item line has no ISO date."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Next\n- [ ] no-date-item\n")
        result = parse_roadmap_items_with_dates(roadmap, "next")
        assert result[0][1] is None

    def test_empty_on_missing_file(self, tmp_path):
        """Returns [] when file does not exist."""
        result = parse_roadmap_items_with_dates(tmp_path / "MISSING.md", "next")
        assert result == []

    def test_empty_on_missing_section(self, tmp_path):
        """Returns [] when named section is absent."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Now\n- [ ] thing\n")
        result = parse_roadmap_items_with_dates(roadmap, "next")
        assert result == []

    def test_multiple_dates_takes_first(self, tmp_path):
        """When multiple dates appear in one item, the first is returned."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Next\n- [ ] item 2025-01-01 2025-06-01\n")
        result = parse_roadmap_items_with_dates(roadmap, "next")
        assert result[0][1] == datetime.date(2025, 1, 1)
