"""Tests for read_roadmap_cached delegating to CacheManager (mtime invalidation)."""

import os
import sys
import time

sys_path = os.path.join(os.path.dirname(__file__), "../../hooks")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)
from utils_cache import CacheManager, get_cache_manager
from utils_roadmap import read_roadmap_cached


class TestReadRoadmapCached:
    def test_hit_returns_content(self, tmp_path):
        """Cache warm — returns cached content without re-reading disk."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Now\n- [ ] feature\n")
        # Write via CacheManager to warm cache
        cache = get_cache_manager(tmp_path)
        # Reset singleton so we get fresh state
        import utils_cache

        utils_cache._cache_manager = CacheManager(tmp_path / ".zie" / "cache")
        cache = utils_cache._cache_manager
        cache.set("roadmap", "cached content", "sess1", ttl=600, invalidation="mtime", source_path=str(roadmap))
        result = read_roadmap_cached(roadmap, "sess1", cwd=tmp_path)
        assert result == "cached content"

    def test_miss_reads_disk(self, tmp_path):
        """Cold cache — reads disk and caches via CacheManager."""
        import utils_cache

        utils_cache._cache_manager = None  # Reset singleton
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("## Now\n- [ ] feature\n")
        result = read_roadmap_cached(roadmap, "sess2", cwd=tmp_path)
        assert result == "## Now\n- [ ] feature\n"
        # Verify cached via get_cache_manager (same singleton)
        cache = get_cache_manager(tmp_path)
        assert cache.get("roadmap", "sess2") == "## Now\n- [ ] feature\n"

    def test_missing_roadmap_returns_empty(self, tmp_path):
        """ROADMAP.md absent — returns empty string."""
        import utils_cache

        utils_cache._cache_manager = None  # Reset singleton
        roadmap = tmp_path / "ROADMAP.md"
        result = read_roadmap_cached(roadmap, "sess3", cwd=tmp_path)
        assert result == ""

    def test_mtime_invalidation(self, tmp_path):
        """Cache invalidated when ROADMAP.md mtime changes."""
        import utils_cache

        utils_cache._cache_manager = None  # Reset singleton
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("original content")
        result1 = read_roadmap_cached(roadmap, "sess4", cwd=tmp_path)
        assert result1 == "original content"
        # Modify file (advance mtime)
        time.sleep(0.05)
        roadmap.write_text("modified content")
        # Need fresh CacheManager instance to see mtime change
        utils_cache._cache_manager = None
        result2 = read_roadmap_cached(roadmap, "sess4", cwd=tmp_path)
        assert result2 == "modified content"
