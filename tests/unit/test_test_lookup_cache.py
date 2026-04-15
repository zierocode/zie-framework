#!/usr/bin/env python3
"""Unit tests for TestLookupCache in hooks/auto-test.py."""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Load auto-test.py directly (hyphen in filename prevents normal import)
hooks_dir = Path(__file__).parent.parent.parent / "hooks"
auto_test_path = hooks_dir / "auto-test.py"
spec = importlib.util.spec_from_file_location("auto_test", auto_test_path)
auto_test_module = importlib.util.module_from_spec(spec)
sys.modules["auto_test"] = auto_test_module
spec.loader.exec_module(auto_test_module)

TestLookupCache = auto_test_module.TestLookupCache

# Import utils_cache normally for get_cache_manager
from hooks import utils_cache  # noqa: E402


@pytest.fixture
def cache_dir():
    """Create a temporary cache directory for each test."""
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def test_lookup_cache(cache_dir, monkeypatch):
    """Create a TestLookupCache instance with temp directory."""
    # Patch get_cache_manager to use our temp cache_dir
    def mock_get_cache_manager(cwd):
        return utils_cache.CacheManager(cache_dir)

    monkeypatch.setattr(auto_test_module, "get_cache_manager", mock_get_cache_manager)
    session_id = "test_session_123"
    return TestLookupCache(session_id, cache_dir)


class TestTestLookupCacheInit:
    """Test TestLookupCache initialization."""

    def test_init_creates_cache_manager(self, cache_dir, monkeypatch):
        """CacheManager is initialized correctly."""
        def mock_get_cache_manager(cwd):
            return utils_cache.CacheManager(cache_dir)

        monkeypatch.setattr(auto_test_module, "get_cache_manager", mock_get_cache_manager)
        cache = TestLookupCache("test_session", cache_dir)
        assert cache.session_id == "test_session"
        assert cache.cwd == cache_dir


class TestTestLookupCacheKeyGeneration:
    """Test cache key generation."""

    def test_source_key_generation(self, test_lookup_cache):
        """Source keys are sanitized correctly."""
        key = test_lookup_cache._source_key("/path/to/test_file.py")
        assert key == "test_source:-path-to-test-file-py"

    def test_source_key_special_chars(self, test_lookup_cache):
        """Special characters are sanitized."""
        key = test_lookup_cache._source_key("src/components/Button.tsx")
        assert "src-components-Button-tsx" in key

    def test_debounce_key_generation(self, test_lookup_cache):
        """Debounce keys are generated correctly."""
        key = test_lookup_cache._debounce_key("/path/to/file.py")
        assert key == "test_debounce:-path-to-file-py"

    def test_test_hash_key_generation(self, test_lookup_cache):
        """Test hash keys are generated correctly."""
        key = test_lookup_cache._test_hash_key("/path/to/test_file.py")
        assert key == "test_hash:-path-to-test-file-py"


class TestTestLookupCacheGetTestForSource:
    """Test get_test_for_source method."""

    def test_cache_miss_returns_none(self, test_lookup_cache):
        """Cache miss returns None."""
        result = test_lookup_cache.get_test_for_source("/nonexistent/file.py")
        assert result is None

    def test_cache_hit_returns_test_path(self, test_lookup_cache, cache_dir):
        """Cache hit returns cached test path."""
        test_file = cache_dir / "tests" / "test_file.py"
        test_file.parent.mkdir(parents=True)
        test_file.touch()

        test_lookup_cache.cache.set(
            test_lookup_cache._source_key("/src/file.py"),
            str(test_file),
            test_lookup_cache.session_id,
            ttl=60,
        )

        result = test_lookup_cache.get_test_for_source("/src/file.py")
        assert result == str(test_file)

    def test_cache_hit_deleted_if_test_missing(self, test_lookup_cache, cache_dir):
        """Cache hit is deleted if test file no longer exists."""
        test_file = cache_dir / "tests" / "test_file.py"
        test_file.parent.mkdir(parents=True)
        # Don't create the file - simulate deletion

        test_lookup_cache.cache.set(
            test_lookup_cache._source_key("/src/file.py"),
            str(test_file),
            test_lookup_cache.session_id,
            ttl=60,
        )

        result = test_lookup_cache.get_test_for_source("/src/file.py")
        assert result is None
        # Cache entry should be deleted
        cached = test_lookup_cache.cache.get(
            test_lookup_cache._source_key("/src/file.py"),
            test_lookup_cache.session_id,
        )
        assert cached is None


class TestTestLookupCacheSetTestMapping:
    """Test set_test_mapping method."""

    def test_set_mapping_stores_test_path(self, test_lookup_cache, cache_dir):
        """set_test_mapping stores the test path."""
        test_file = cache_dir / "tests" / "test_file.py"
        test_file.parent.mkdir(parents=True)
        test_file.touch()

        test_lookup_cache.set_test_mapping("/src/file.py", str(test_file))

        result = test_lookup_cache.get_test_for_source("/src/file.py")
        assert result == str(test_file)

    def test_set_mapping_stores_test_hash(self, test_lookup_cache, cache_dir):
        """set_test_mapping also stores test file hash."""
        test_file = cache_dir / "tests" / "test_file.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("test content")

        test_lookup_cache.set_test_mapping("/src/file.py", str(test_file))

        hash_key = test_lookup_cache._test_hash_key(str(test_file))
        cached_hash = test_lookup_cache.cache.get(hash_key, test_lookup_cache.session_id)
        assert cached_hash is not None
        assert "hash" in cached_hash
        assert "path" in cached_hash

    def test_set_mapping_handles_missing_test_file(self, test_lookup_cache, cache_dir):
        """set_test_mapping handles missing test file gracefully."""
        test_file = cache_dir / "tests" / "test_file.py"
        # Don't create the file

        # Should not raise
        test_lookup_cache.set_test_mapping("/src/file.py", str(test_file))


class TestTestLookupCacheInvalidateOnTestChange:
    """Test invalidate_on_test_change method."""

    def test_no_cache_entry_returns_false(self, test_lookup_cache):
        """No cache entry returns False."""
        result = test_lookup_cache.invalidate_on_test_change("/nonexistent/test.py")
        assert result is False

    def test_test_file_missing_returns_false(self, test_lookup_cache, cache_dir):
        """Missing test file returns False."""
        test_file = cache_dir / "tests" / "test_file.py"
        test_file.parent.mkdir(parents=True)
        # Don't create the file

        test_lookup_cache.cache.set(
            test_lookup_cache._test_hash_key(str(test_file)),
            {"hash": "abc123", "path": str(test_file)},
            test_lookup_cache.session_id,
            ttl=60,
        )

        result = test_lookup_cache.invalidate_on_test_change(str(test_file))
        assert result is False

    def test_test_file_changed_returns_true(self, test_lookup_cache, cache_dir):
        """Changed test file returns True (invalidated)."""
        test_file = cache_dir / "tests" / "test_file.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("original content")

        # Set initial hash
        test_lookup_cache.set_test_mapping("/src/file.py", str(test_file))

        # Change test file content
        test_file.write_text("modified content")

        result = test_lookup_cache.invalidate_on_test_change(str(test_file))
        assert result is True

    def test_test_file_unchanged_returns_false(self, test_lookup_cache, cache_dir):
        """Unchanged test file returns False."""
        test_file = cache_dir / "tests" / "test_file.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("unchanged content")

        # Set initial hash
        test_lookup_cache.set_test_mapping("/src/file.py", str(test_file))

        # No change
        result = test_lookup_cache.invalidate_on_test_change(str(test_file))
        assert result is False


class TestTestLookupCacheDebounce:
    """Test per-file debounce logic."""

    def test_should_debounce_false_on_cache_miss(self, test_lookup_cache):
        """Cache miss returns False (no debounce)."""
        result = test_lookup_cache.should_debounce("/src/file.py")
        assert result is False

    def test_should_debounce_true_within_window(self, test_lookup_cache):
        """Within debounce window returns True."""
        test_lookup_cache.mark_tested("/src/file.py")

        # Immediately check - should be within 5000ms window
        result = test_lookup_cache.should_debounce("/src/file.py")
        assert result is True

    def test_should_debounce_false_after_window(self, test_lookup_cache):
        """After debounce window returns False."""
        # Manually set old timestamp
        test_lookup_cache.cache.set(
            test_lookup_cache._debounce_key("/src/file.py"),
            {"last_tested": time.time() - 10, "path": "/src/file.py"},
            test_lookup_cache.session_id,
            ttl=60,
        )

        result = test_lookup_cache.should_debounce("/src/file.py")
        assert result is False

    def test_mark_tested_sets_timestamp(self, test_lookup_cache):
        """mark_tested sets last_tested timestamp."""
        before = time.time()
        test_lookup_cache.mark_tested("/src/file.py")
        after = time.time()

        cached = test_lookup_cache.cache.get(
            test_lookup_cache._debounce_key("/src/file.py"),
            test_lookup_cache.session_id,
        )
        assert cached is not None
        assert "last_tested" in cached
        assert before <= cached["last_tested"] <= after
        assert cached["path"] == "/src/file.py"


class TestTestLookupCacheIntegration:
    """Test full integration workflow."""

    def test_full_workflow(self, test_lookup_cache, cache_dir):
        """Full cache workflow: miss → set → hit → debounce."""
        test_file = cache_dir / "tests" / "test_file.py"
        test_file.parent.mkdir(parents=True)
        test_file.touch()

        source_path = "/src/file.py"

        # 1. Cache miss
        result = test_lookup_cache.get_test_for_source(source_path)
        assert result is None

        # 2. Set mapping
        test_lookup_cache.set_test_mapping(source_path, str(test_file))

        # 3. Cache hit
        result = test_lookup_cache.get_test_for_source(source_path)
        assert result == str(test_file)

        # 4. Mark as tested (debounce)
        test_lookup_cache.mark_tested(source_path)

        # 5. Should debounce
        assert test_lookup_cache.should_debounce(source_path) is True
