#!/usr/bin/env python3
"""Unit tests for CacheManager in hooks/utils_cache.py."""
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Import after sys.path setup in conftest
from hooks.utils_cache import CacheManager, get_cache_manager, get_playwright_version_cached, _cache_manager


@pytest.fixture
def cache_dir():
    """Create a temporary cache directory for each test."""
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def cache_manager(cache_dir):
    """Create a CacheManager instance with temp directory."""
    return CacheManager(cache_dir)


class TestCacheManagerInit:
    """Test CacheManager initialization."""

    def test_init_creates_cache_dir(self, cache_dir):
        """Cache directory is created if it doesn't exist."""
        nested = cache_dir / "nested" / "cache"
        manager = CacheManager(nested)
        assert nested.exists()
        assert manager.cache_dir == nested

    def test_init_loads_existing_cache(self, cache_dir):
        """Existing cache file is loaded on init."""
        cache_file = cache_dir / "session-cache.json"
        test_data = {"session:test:key": {"value": "test_value", "expires_at": time.time() + 100}}
        cache_file.write_text(json.dumps(test_data))

        manager = CacheManager(cache_dir)
        assert manager._cache == test_data

    def test_init_handles_corrupt_cache(self, cache_dir):
        """Corrupt cache file is handled gracefully."""
        cache_file = cache_dir / "session-cache.json"
        cache_file.write_text("not valid json")

        manager = CacheManager(cache_dir)
        assert manager._cache == {}


class TestCacheManagerSetGet:
    """Test CacheManager set and get operations."""

    def test_set_and_get(self, cache_manager):
        """Basic set and get works."""
        cache_manager.set("test_key", "test_value", "session123", ttl=60)
        result = cache_manager.get("test_key", "session123")
        assert result == "test_value"

    def test_get_missing_key(self, cache_manager):
        """Get returns None for missing key."""
        result = cache_manager.get("nonexistent", "session123")
        assert result is None

    def test_session_isolation(self, cache_manager):
        """Different sessions have isolated caches."""
        cache_manager.set("key", "value_session1", "session1", ttl=60)
        cache_manager.set("key", "value_session2", "session2", ttl=60)

        assert cache_manager.get("key", "session1") == "value_session1"
        assert cache_manager.get("key", "session2") == "value_session2"

    def test_special_characters_in_session_id(self, cache_manager):
        """Session IDs with special characters are handled."""
        session_id = "test@#$%session-123"
        cache_manager.set("key", "value", session_id, ttl=60)
        assert cache_manager.get("key", session_id) == "value"


class TestCacheManagerTTL:
    """Test TTL expiration logic."""

    def test_ttl_expiration(self, cache_manager):
        """Expired entries return None."""
        cache_manager.set("key", "value", "session123", ttl=1)
        time.sleep(1.1)  # Wait for expiration
        result = cache_manager.get("key", "session123")
        assert result is None

    def test_ttl_not_expired(self, cache_manager):
        """Non-expired entries are returned."""
        cache_manager.set("key", "value", "session123", ttl=60)
        result = cache_manager.get("key", "session123")
        assert result == "value"

    def test_ttl_entry_removed_on_read(self, cache_manager):
        """Expired entries are removed on read."""
        cache_manager.set("key", "value", "session123", ttl=1)
        time.sleep(1.1)
        cache_manager.get("key", "session123")  # Trigger lazy deletion
        assert f"session:session123:key" not in cache_manager._cache


class TestCacheManagerDelete:
    """Test delete operations."""

    def test_delete_existing_key(self, cache_manager):
        """Delete removes existing key."""
        cache_manager.set("key", "value", "session123", ttl=60)
        cache_manager.delete("key", "session123")
        result = cache_manager.get("key", "session123")
        assert result is None

    def test_delete_nonexistent_key(self, cache_manager):
        """Delete on nonexistent key doesn't raise."""
        cache_manager.delete("nonexistent", "session123")  # Should not raise


class TestCacheManagerClearSession:
    """Test clear_session operations."""

    def test_clear_session_removes_all_keys(self, cache_manager):
        """Clear session removes all keys for that session."""
        cache_manager.set("key1", "value1", "session1", ttl=60)
        cache_manager.set("key2", "value2", "session1", ttl=60)
        cache_manager.set("key3", "value3", "session2", ttl=60)

        cache_manager.clear_session("session1")

        assert cache_manager.get("key1", "session1") is None
        assert cache_manager.get("key2", "session1") is None
        assert cache_manager.get("key3", "session2") == "value3"  # Other session unaffected

    def test_clear_session_with_no_keys(self, cache_manager):
        """Clear session with no keys doesn't raise."""
        cache_manager.clear_session("nonexistent")  # Should not raise


class TestCacheManagerGetOrCompute:
    """Test get_or_compute helper."""

    def test_get_or_compute_cache_miss(self, cache_manager):
        """Compute function is called on cache miss."""
        call_count = [0]

        def compute_fn():
            call_count[0] += 1
            return "computed_value"

        result = cache_manager.get_or_compute("key", "session123", compute_fn, ttl=60)
        assert result == "computed_value"
        assert call_count[0] == 1

    def test_get_or_compute_cache_hit(self, cache_manager):
        """Compute function is NOT called on cache hit."""
        cache_manager.set("key", "cached_value", "session123", ttl=60)
        call_count = [0]

        def compute_fn():
            call_count[0] += 1
            return "computed_value"

        result = cache_manager.get_or_compute("key", "session123", compute_fn, ttl=60)
        assert result == "cached_value"
        assert call_count[0] == 0  # Not called

    def test_get_or_compute_caches_result(self, cache_manager):
        """get_or_compute stores result in cache."""
        call_count = [0]

        def compute_fn():
            call_count[0] += 1
            return "computed_value"

        # First call - cache miss
        result1 = cache_manager.get_or_compute("key", "session123", compute_fn, ttl=60)
        # Second call - cache hit
        result2 = cache_manager.get_or_compute("key", "session123", compute_fn, ttl=60)

        assert result1 == "computed_value"
        assert result2 == "computed_value"
        assert call_count[0] == 1  # Only called once


class TestCacheManagerPersistence:
    """Test cache persistence to disk."""

    def test_save_persists_to_disk(self, cache_manager):
        """Cache is persisted to disk."""
        cache_manager.set("key", "value", "session123", ttl=60)

        # Read cache file directly
        cache_content = json.loads(cache_manager.cache_file.read_text())
        assert "session:session123:key" in cache_content
        assert cache_content["session:session123:key"]["value"] == "value"

    def test_load_from_disk(self, cache_dir):
        """Cache is loaded from disk on init."""
        # Write cache file directly
        cache_file = cache_dir / "session-cache.json"
        test_data = {"session:test:key": {"value": "disk_value", "expires_at": time.time() + 100}}
        cache_file.write_text(json.dumps(test_data))

        # Create new manager (loads from disk)
        manager = CacheManager(cache_dir)
        assert manager.get("key", "test") == "disk_value"


class TestCacheManagerConcurrency:
    """Test concurrent access safety."""

    def test_concurrent_access(self, cache_manager):
        """Multiple operations don't corrupt cache."""
        import threading

        errors = []

        def worker(session_id):
            try:
                for i in range(10):
                    cache_manager.set(f"key_{i}", f"value_{i}", session_id, ttl=60)
                    cache_manager.get(f"key_{i}", session_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(f"session_{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestGetCacheManager:
    """Test get_cache_manager singleton."""

    def test_singleton_pattern(self, cache_dir, monkeypatch):
        """get_cache_manager returns same instance."""
        monkeypatch.setattr("hooks.utils_cache._cache_manager", None)

        # Mock cwd
        with patch.object(Path, "cwd", return_value=cache_dir):
            manager1 = get_cache_manager(cache_dir)
            manager2 = get_cache_manager(cache_dir)
            assert manager1 is manager2


class TestCacheTTLs:
    """Test CACHE_TTLS configuration."""

    def test_cache_ttls_values(self):
        """CACHE_TTLS has expected keys and reasonable values."""
        from hooks.utils_config import CACHE_TTLS

        assert "roadmap" in CACHE_TTLS
        assert "adrs" in CACHE_TTLS
        assert "project_md" in CACHE_TTLS
        assert "content_hash" in CACHE_TTLS

        # Verify reasonable TTL values (in seconds)
        assert 60 <= CACHE_TTLS["roadmap"] <= 3600  # 1 min to 1 hour
        assert 60 <= CACHE_TTLS["adrs"] <= 7200  # 1 min to 2 hours
        assert 60 <= CACHE_TTLS["project_md"] <= 1800  # 1 min to 30 min

    def test_content_hash_ttl_is_1800(self):
        """Content-hash TTL is 1800s (30 minutes) as per content-hash-ttl-increase."""
        from hooks.utils_config import CACHE_TTLS

        assert CACHE_TTLS["content_hash"] == 1800


class TestGetContentHashCached:
    """Test get_content_hash_cached helper."""

    def test_content_hash_computation(self, cache_dir, monkeypatch):
        """Content hash is computed correctly."""
        from hooks.utils_cache import get_content_hash_cached

        # Set up global cache manager
        monkeypatch.setattr("hooks.utils_cache._cache_manager", None)

        # Create test files
        decisions_dir = cache_dir / "zie-framework" / "decisions"
        decisions_dir.mkdir(parents=True)
        (decisions_dir / "ADR-000-summary.md").write_text("# ADR Summary\n\nTest content")

        context_dir = cache_dir / "zie-framework" / "project"
        context_dir.mkdir(parents=True)
        (context_dir / "context.md").write_text("# Project Context\n\nTest context")

        # Compute hash
        result = get_content_hash_cached(cache_dir, "test_session")

        # Verify hash is non-empty hex string
        assert len(result) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in result)

    def test_content_hash_session_isolation(self, cache_dir, monkeypatch):
        """Different sessions get same hash (content-based, not session-based)."""
        from hooks.utils_cache import get_content_hash_cached

        monkeypatch.setattr("hooks.utils_cache._cache_manager", None)

        # Create test files
        decisions_dir = cache_dir / "zie-framework" / "decisions"
        decisions_dir.mkdir(parents=True)
        (decisions_dir / "ADR-000-summary.md").write_text("# ADR Summary\n\nTest content")

        context_dir = cache_dir / "zie-framework" / "project"
        context_dir.mkdir(parents=True)
        (context_dir / "context.md").write_text("# Project Context\n\nTest context")

        hash1 = get_content_hash_cached(cache_dir, "session1")
        hash2 = get_content_hash_cached(cache_dir, "session2")

        # Hash is content-based, so same content = same hash
        assert hash1 == hash2

    def test_content_hash_missing_files(self, cache_dir, monkeypatch):
        """Returns empty string when files don't exist."""
        from hooks.utils_cache import get_content_hash_cached

        monkeypatch.setattr("hooks.utils_cache._cache_manager", None)

        # No files created
        result = get_content_hash_cached(cache_dir, "test_session")
        assert result == ""


# ── Playwright version cache tests ────────────────────────────────────────────


class TestPlaywrightVersionCache:
    """Tests for get_playwright_version_cached() in utils_cache.py."""

    def test_cache_miss_calls_subprocess(self, cache_dir, monkeypatch):
        """On cache miss, subprocess is called and result is cached."""
        monkeypatch.setattr("hooks.utils_cache._cache_manager", None)
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: type("R", (), {"stdout": "1.55.1\n"})(),
        )
        result = get_playwright_version_cached("sess1", cache_dir)
        assert result == "1.55.1"

    def test_cache_hit_skips_subprocess(self, cache_dir, monkeypatch):
        """On cache hit, subprocess is not called."""
        monkeypatch.setattr("hooks.utils_cache._cache_manager", None)
        call_count = {"n": 0}

        def fake_run(*a, **kw):
            call_count["n"] += 1
            return type("R", (), {"stdout": "1.55.1\n"})()

        monkeypatch.setattr("subprocess.run", fake_run)

        # First call: cache miss, subprocess called
        r1 = get_playwright_version_cached("sess2", cache_dir)
        assert r1 == "1.55.1"
        assert call_count["n"] == 1

        # Reset manager to simulate same session (cache on disk)
        monkeypatch.setattr("hooks.utils_cache._cache_manager", None)
        result2 = get_playwright_version_cached("sess2", cache_dir)
        assert result2 == "1.55.1"
        # Subprocess should not have been called again
        assert call_count["n"] == 1

    def test_subprocess_failure_returns_empty(self, cache_dir, monkeypatch):
        """FileNotFoundError should return empty string, no cache entry."""
        monkeypatch.setattr("hooks.utils_cache._cache_manager", None)
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError()),
        )
        result = get_playwright_version_cached("sess3", cache_dir)
        assert result == ""

    def test_subprocess_timeout_returns_empty(self, cache_dir, monkeypatch):
        """Timeout should return empty string, no cache entry."""
        import subprocess as sp
        monkeypatch.setattr("hooks.utils_cache._cache_manager", None)
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: (_ for _ in ()).throw(sp.TimeoutExpired(cmd="playwright", timeout=5)),
        )
        result = get_playwright_version_cached("sess4", cache_dir)
        assert result == ""
