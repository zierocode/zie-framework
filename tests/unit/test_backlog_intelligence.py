"""Tests for backlog auto-tag keyword matching and duplicate detection logic."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
from utils_backlog import find_duplicate_slugs, infer_tag

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
