"""Tests for CacheManager: TTL, mtime, and session invalidation modes."""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
from utils_cache import CacheManager


class TestTTLInvalidation:
    """Default TTL-based invalidation (existing behavior)."""

    def test_set_get_roundtrip(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set("key1", "val1", "sess1", ttl=600)
        assert cache.get("key1", "sess1") == "val1"

    def test_expired_entry_returns_none(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set("key1", "val1", "sess1", ttl=0)
        # ttl=0 means already expired (expires_at = time.time() + 0)
        # Allow tiny time delta
        time.sleep(0.01)
        assert cache.get("key1", "sess1") is None

    def test_session_isolation(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set("key1", "val_a", "sess_a", ttl=600)
        cache.set("key1", "val_b", "sess_b", ttl=600)
        assert cache.get("key1", "sess_a") == "val_a"
        assert cache.get("key1", "sess_b") == "val_b"

    def test_delete_removes_entry(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set("key1", "val1", "sess1", ttl=600)
        cache.delete("key1", "sess1")
        assert cache.get("key1", "sess1") is None

    def test_clear_session_removes_entries(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set("key1", "val1", "sess1", ttl=600)
        cache.set("key2", "val2", "sess1", ttl=600)
        cache.set("key3", "val3", "sess2", ttl=600)
        cache.clear_session("sess1")
        assert cache.get("key1", "sess1") is None
        assert cache.get("key2", "sess1") is None
        assert cache.get("key3", "sess2") == "val3"

    def test_get_or_compute_caches(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        calls = 0

        def compute():
            nonlocal calls
            calls += 1
            return "computed"

        result = cache.get_or_compute("key1", "sess1", compute, ttl=600)
        assert result == "computed"
        assert calls == 1
        # Second call should use cache
        result2 = cache.get_or_compute("key1", "sess1", compute, ttl=600)
        assert result2 == "computed"
        assert calls == 1  # compute not called again


class TestMtimeInvalidation:
    """mtime invalidation — invalidate when source file changes."""

    def test_mtime_hit(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        src = tmp_path / "source.txt"
        src.write_text("original")
        cache.set("doc", "content", "sess1", ttl=600, invalidation="mtime", source_path=str(src))
        assert cache.get("doc", "sess1") == "content"

    def test_mtime_invalidate_on_change(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        src = tmp_path / "source.txt"
        src.write_text("original")
        cache.set("doc", "content", "sess1", ttl=600, invalidation="mtime", source_path=str(src))
        # Modify the file (advance mtime)
        time.sleep(0.05)
        src.write_text("modified")
        # Cache should be invalidated
        assert cache.get("doc", "sess1") is None

    def test_mtime_preserves_if_unchanged(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        src = tmp_path / "source.txt"
        src.write_text("original")
        cache.set("doc", "content", "sess1", ttl=600, invalidation="mtime", source_path=str(src))
        # Read again without modifying — should still be cached
        assert cache.get("doc", "sess1") == "content"

    def test_mtime_source_path_missing(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        src = tmp_path / "nonexistent.txt"
        cache.set("doc", "content", "sess1", ttl=600, invalidation="mtime", source_path=str(src))
        # File doesn't exist — should be invalidated
        assert cache.get("doc", "sess1") is None

    def test_mtime_requires_source_path(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        with pytest.raises(ValueError, match="source_path is required"):
            cache.set("doc", "content", "sess1", ttl=600, invalidation="mtime")

    def test_get_or_compute_with_mtime(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        src = tmp_path / "source.txt"
        src.write_text("original")
        calls = 0

        def compute():
            nonlocal calls
            calls += 1
            return src.read_text()

        result = cache.get_or_compute(
            "doc",
            "sess1",
            compute,
            ttl=600,
            invalidation="mtime",
            source_path=str(src),
        )
        assert result == "original"
        assert calls == 1
        # Second call — same mtime, should use cache
        result2 = cache.get_or_compute(
            "doc",
            "sess1",
            compute,
            ttl=600,
            invalidation="mtime",
            source_path=str(src),
        )
        assert result2 == "original"
        assert calls == 1  # compute not called again

    def test_get_or_compute_mtime_invalidate(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        src = tmp_path / "source.txt"
        src.write_text("original")
        calls = 0

        def compute():
            nonlocal calls
            calls += 1
            return src.read_text()

        cache.get_or_compute(
            "doc",
            "sess1",
            compute,
            ttl=600,
            invalidation="mtime",
            source_path=str(src),
        )
        assert calls == 1
        # Modify file
        time.sleep(0.05)
        src.write_text("modified")
        cache2 = CacheManager(tmp_path / "cache")
        result = cache2.get_or_compute(
            "doc",
            "sess1",
            compute,
            ttl=600,
            invalidation="mtime",
            source_path=str(src),
        )
        assert result == "modified"
        assert calls == 2


class TestSessionInvalidation:
    """session invalidation — persists until clear_session()."""

    def test_session_entry_persists(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set("flag", True, "sess1", ttl=0, invalidation="session")
        # Should not expire even with ttl=0
        assert cache.get("flag", "sess1") is True

    def test_session_cleared_by_clear_session(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set("flag", True, "sess1", ttl=0, invalidation="session")
        cache.clear_session("sess1")
        assert cache.get("flag", "sess1") is None

    def test_session_does_not_affect_other_session(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set("flag", True, "sess1", ttl=0, invalidation="session")
        cache.set("flag", True, "sess2", ttl=0, invalidation="session")
        cache.clear_session("sess1")
        assert cache.get("flag", "sess1") is None
        assert cache.get("flag", "sess2") is True


class TestSetFlagHasFlag:
    """set_flag / has_flag — lightweight boolean helpers."""

    def test_set_flag_and_has_flag(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set_flag("compact-tier-1", "sess1")
        assert cache.has_flag("compact-tier-1", "sess1") is True

    def test_has_flag_returns_false_for_missing(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        assert cache.has_flag("nonexistent", "sess1") is False

    def test_flag_is_session_scoped(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set_flag("compact-tier-1", "sess1")
        assert cache.has_flag("compact-tier-1", "sess1") is True
        assert cache.has_flag("compact-tier-1", "sess2") is False

    def test_flag_cleared_by_clear_session(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set_flag("compact-tier-1", "sess1")
        cache.clear_session("sess1")
        assert cache.has_flag("compact-tier-1", "sess1") is False

    def test_clear_session_does_not_affect_other_session_flags(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        cache.set_flag("compact-tier-1", "sess1")
        cache.set_flag("compact-tier-1", "sess2")
        cache.clear_session("sess1")
        assert cache.has_flag("compact-tier-1", "sess1") is False
        assert cache.has_flag("compact-tier-1", "sess2") is True

    def test_flag_survives_reload(self, tmp_path):
        cache1 = CacheManager(tmp_path / "cache")
        cache1.set_flag("compact-tier-1", "sess1")
        # Simulate restart by creating a new instance
        cache2 = CacheManager(tmp_path / "cache")
        assert cache2.has_flag("compact-tier-1", "sess1") is True
