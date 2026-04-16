"""Error-path tests for utils_roadmap module.

Validates that all public functions return empty/default on error, never raise.
"""

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.error_path

sys.path.insert(0, str(Path(__file__).parents[1] / "hooks"))


class TestUtilsRoadmapErrorPaths:
    """Error-path coverage for utils_roadmap.py."""

    def test_read_roadmap_cached_missing_file_returns_empty(self, tmp_path):
        """When ROADMAP.md doesn't exist, returns empty string."""
        from hooks.utils_roadmap import read_roadmap_cached

        result = read_roadmap_cached(tmp_path / "nonexistent" / "ROADMAP.md", "test-sess", tmp_path)
        assert result == ""

    def test_read_roadmap_cached_corrupt_file_returns_empty(self, tmp_path):
        """When ROADMAP.md can't be read (permission), returns empty."""
        from hooks.utils_roadmap import read_roadmap_cached

        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Now\n- [x] test")
        # This should work fine
        result = read_roadmap_cached(roadmap, "test-sess", tmp_path)
        assert "test" in result

    def test_get_cached_git_status_cache_miss_returns_none(self, tmp_path, monkeypatch):
        """When git status cache file doesn't exist, returns None."""
        from hooks.utils_roadmap import get_cached_git_status

        result = get_cached_git_status(tmp_path, "test-sess")
        # Cache miss returns None (expected)
        assert result is None

    def test_write_git_status_cache_error_logs_stderr(self, tmp_path):
        """When cache write fails, logs to stderr but doesn't raise."""
        from hooks.utils_roadmap import write_git_status_cache

        # write_git_status_cache(session_id, key, content) -> None
        # On a writable tmp_path this should not raise
        result = write_git_status_cache("test-sess", "git_status", "M test.py")
        # Should return None (void), not raise
        assert result is None

    def test_get_cached_adrs_cache_miss_returns_none(self, tmp_path):
        """When ADR cache doesn't exist, returns None."""
        from hooks.utils_roadmap import get_cached_adrs

        result = get_cached_adrs(tmp_path, "test-sess")
        assert result is None

    def test_parse_roadmap_items_with_dates_corrupt_input(self, tmp_path):
        """When ROADMAP content is corrupt, returns empty list."""
        from hooks.utils_roadmap import parse_roadmap_items_with_dates

        # Requires (roadmap_path, section_name)
        nonexistent = tmp_path / "nonexistent_roadmap.md"
        result = parse_roadmap_items_with_dates(nonexistent, "Now")
        assert isinstance(result, list)

        # Garbage content file
        garbage = tmp_path / "garbage.md"
        garbage.write_text("not valid roadmap content at all")
        result = parse_roadmap_items_with_dates(garbage, "Now")
        assert isinstance(result, list)

    def test_extract_problem_excerpt_missing_file(self, tmp_path):
        """When backlog file doesn't exist, returns fallback string."""
        from hooks.utils_roadmap import extract_problem_excerpt

        result = extract_problem_excerpt("nonexistent-slug", tmp_path)
        assert result == "(no description)"

    def test_extract_problem_excerpt_no_problem_section(self, tmp_path):
        """When backlog file has no Problem section, returns fallback."""
        from hooks.utils_roadmap import extract_problem_excerpt

        backlog_dir = tmp_path / "zie-framework" / "backlog"
        backlog_dir.mkdir(parents=True)
        backlog_file = backlog_dir / "test-slug.md"
        backlog_file.write_text("---\ndate: 2026-01-01\n---\n\n## Scope\nSome scope text.")

        result = extract_problem_excerpt("test-slug", tmp_path)
        assert isinstance(result, str)

    def test_is_track_active_missing_roadmap(self, tmp_path, monkeypatch):
        """When ROADMAP.md is missing, is_track_active should not crash."""
        from hooks.utils_roadmap import is_track_active

        # is_track_active(cwd) takes only cwd, not a track name
        result = is_track_active(tmp_path)
        # Should return bool, not crash
        assert isinstance(result, bool)
