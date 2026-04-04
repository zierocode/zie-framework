"""Tests for mtime-gated ROADMAP cache in utils_roadmap.py."""
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
from utils_roadmap import get_cached_roadmap, read_roadmap_cached, write_roadmap_cache


class TestGetCachedRoadmap:
    def test_cache_hit(self, tmp_path):
        """Cache hit when mtime matches exactly."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Now\n- [ ] feature\n")
        write_roadmap_cache("sess1", "cached content", roadmap, tmp_dir=tmp_path)
        result = get_cached_roadmap("sess1", roadmap, tmp_dir=tmp_path)
        assert result == "cached content"

    def test_cache_miss_on_mtime_change(self, tmp_path):
        """Cache miss when ROADMAP.md mtime changes after write."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Now\n- [ ] feature\n")
        write_roadmap_cache("sess2", "cached content", roadmap, tmp_dir=tmp_path)
        # Touch the file to advance mtime
        time.sleep(0.01)
        roadmap.write_text("## Now\n- [ ] updated\n")
        result = get_cached_roadmap("sess2", roadmap, tmp_dir=tmp_path)
        assert result is None

    def test_cache_miss_on_no_file(self, tmp_path):
        """Cache miss when no cache file exists."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Now\n")
        result = get_cached_roadmap("sess3", roadmap, tmp_dir=tmp_path)
        assert result is None

    def test_write_round_trip(self, tmp_path):
        """write_roadmap_cache + get_cached_roadmap returns original content."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Now\n- [ ] thing\n")
        write_roadmap_cache("sess4", "original content", roadmap, tmp_dir=tmp_path)
        assert get_cached_roadmap("sess4", roadmap, tmp_dir=tmp_path) == "original content"


class TestReadRoadmapCached:
    def test_hit_returns_cached(self, tmp_path):
        """Cache warm — returns cached content without re-reading disk."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("disk content")
        write_roadmap_cache("sess5", "cached content", roadmap, tmp_dir=tmp_path)
        result = read_roadmap_cached(roadmap, "sess5", tmp_dir=tmp_path)
        assert result == "cached content"

    def test_miss_reads_disk(self, tmp_path):
        """Cold cache — reads disk and warms cache."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("disk content")
        result = read_roadmap_cached(roadmap, "sess6", tmp_dir=tmp_path)
        assert result == "disk content"
        # Cache is now warm
        assert get_cached_roadmap("sess6", roadmap, tmp_dir=tmp_path) == "disk content"

    def test_missing_roadmap_returns_empty(self, tmp_path):
        """ROADMAP.md absent — returns empty string."""
        roadmap = tmp_path / "ROADMAP.md"
        result = read_roadmap_cached(roadmap, "sess7", tmp_dir=tmp_path)
        assert result == ""
