"""Tests for backlog auto-tag keyword matching and duplicate detection logic."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
from utils_backlog import find_duplicate_slugs, find_roadmap_overlaps, infer_tag, is_full_duplicate

TAG_KEYWORD_MAP = {
    "bug": ["fix", "error", "crash", "broken"],
    "chore": ["cleanup", "update", "bump", "refactor"],
    "debt": ["tech debt", "debt", "legacy", "slow"],
    "feature": ["add", "new", "implement", "support"],
}


class TestInferTag:
    def test_bug_tag_on_fix_keyword(self):
        assert infer_tag("fix login error", TAG_KEYWORD_MAP) == "bug"

    def test_chore_tag_on_refactor_keyword(self):
        assert infer_tag("refactor utils module", TAG_KEYWORD_MAP) == "chore"

    def test_debt_tag_on_legacy_keyword(self):
        assert infer_tag("migrate legacy auth system", TAG_KEYWORD_MAP) == "debt"

    def test_feature_tag_on_add_keyword(self):
        assert infer_tag("add CSV export", TAG_KEYWORD_MAP) == "feature"

    def test_default_feature_when_no_match(self):
        assert infer_tag("smarter framework intelligence", TAG_KEYWORD_MAP) == "feature"

    def test_first_match_wins(self):
        assert infer_tag("fix and refactor error handler", TAG_KEYWORD_MAP) == "bug"

    def test_case_insensitive_match(self):
        assert infer_tag("Fix Crash on startup", TAG_KEYWORD_MAP) == "bug"

    def test_empty_title_returns_feature(self):
        assert infer_tag("", TAG_KEYWORD_MAP) == "feature"


class TestFindDuplicateSlugs:
    def test_no_duplicates_when_backlog_empty(self, tmp_path):
        result = find_duplicate_slugs("add-csv-export", tmp_path)
        assert result == []

    def test_detects_two_token_overlap(self, tmp_path):
        (tmp_path / "csv-export-tool.md").write_text("")
        result = find_duplicate_slugs("add-csv-export", tmp_path)
        assert "csv-export-tool" in result

    def test_no_duplicate_on_one_token_overlap(self, tmp_path):
        (tmp_path / "csv-summary.md").write_text("")
        result = find_duplicate_slugs("add-csv-export", tmp_path)
        assert result == []

    def test_ignores_self_match(self, tmp_path):
        (tmp_path / "add-csv-export.md").write_text("")
        result = find_duplicate_slugs("add-csv-export", tmp_path)
        assert "add-csv-export" not in result

    def test_multiple_duplicates_returned(self, tmp_path):
        (tmp_path / "csv-export-tool.md").write_text("")
        (tmp_path / "csv-export-report.md").write_text("")
        result = find_duplicate_slugs("add-csv-export", tmp_path)
        assert len(result) == 2

    def test_title_text_overlap_detected(self, tmp_path):
        """Slug has no overlap but title text does — should still detect."""
        (tmp_path / "data-output.md").write_text("# CSV Export Tool\n\nSome content")
        result = find_duplicate_slugs("add-csv-export", tmp_path)
        assert "data-output" in result


class TestFindRoadmapOverlaps:
    def _write_roadmap(self, path, ready_block="", done_block=""):
        content = f"""# ROADMAP — test

---

## Now — Active Sprint

<!-- -->

---

## Ready — Approved Plans

{ready_block}

---

## Next — Prioritized Backlog

<!-- -->

---

## Done

{done_block}

<!-- -->
"""
        path.write_text(content)

    def test_no_overlap_when_roadmap_empty(self, tmp_path):
        roadmap = tmp_path / "ROADMAP.md"
        self._write_roadmap(roadmap)
        result = find_roadmap_overlaps("CSV Export Tool", roadmap)
        assert result == []

    def test_ready_overlap_detected(self, tmp_path):
        roadmap = tmp_path / "ROADMAP.md"
        self._write_roadmap(roadmap, ready_block="- [ ] csv-tool — CSV Export feature\n")
        result = find_roadmap_overlaps("CSV Export Tool", roadmap)
        assert len(result) >= 1
        assert any("Ready" in r[0] for r in result)

    def test_done_overlap_detected(self, tmp_path):
        roadmap = tmp_path / "ROADMAP.md"
        self._write_roadmap(roadmap, done_block="- [x] csv-output — CSV Export helper\n")
        result = find_roadmap_overlaps("CSV Export Tool", roadmap)
        assert len(result) >= 1
        assert any("Done" in r[0] for r in result)

    def test_single_token_no_overlap(self, tmp_path):
        roadmap = tmp_path / "ROADMAP.md"
        self._write_roadmap(roadmap, ready_block="- [ ] tool — Helper utility\n")
        result = find_roadmap_overlaps("CSV Export", roadmap)
        assert result == []


class TestIsFullDuplicate:
    def test_full_match_returns_true(self, tmp_path):
        (tmp_path / "csv-export.md").write_text("# CSV Export\n\nContent here")
        # All new tokens are contained in existing → full duplicate
        assert is_full_duplicate("CSV Export", "csv-export", "csv-export", tmp_path) is True

    def test_partial_match_returns_false(self, tmp_path):
        (tmp_path / "csv-tool.md").write_text("# CSV Tool\n\nContent here")
        assert is_full_duplicate("CSV Export", "add-csv-export", "csv-tool", tmp_path) is False

    def test_missing_file_returns_false(self, tmp_path):
        assert is_full_duplicate("CSV Export", "add-csv-export", "nonexistent", tmp_path) is False
