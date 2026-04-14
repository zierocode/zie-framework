#!/usr/bin/env python3
"""Unified session-scoped cache manager for zie-framework hooks.

Centralizes ROADMAP, ADRs, and project knowledge caching. Eliminates duplicate
disk reads across 6+ hooks per session.

Cache location: .zie/cache/session-cache.json
Session isolation: keyed by session_id to prevent cross-session pollution.
TTL expiration: time-based expiration per key.
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Optional


class CacheManager:
    """Session-scoped cache manager with TTL support.

    Usage:
        cache = CacheManager(Path(".zie/cache"))
        value = cache.get("roadmap", session_id)
        cache.set("roadmap", content, session_id, ttl=600)

        # Or use cache-or-compute helper:
        value = cache.get_or_compute("roadmap", session_id, compute_fn, ttl=600)
    """

    def __init__(self, cache_dir: Path):
        """Initialize cache directory.

        Args:
            cache_dir: Directory to store cache file (e.g., Path(".zie/cache"))
        """
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "session-cache.json"
        self._cache: dict = {}
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> dict:
        """Load cache from disk. Returns empty dict on miss/error."""
        if not self.cache_file.exists():
            return {}
        try:
            content = self.cache_file.read_text()
            self._cache = json.loads(content)
            return self._cache
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self) -> None:
        """Persist cache to disk atomically."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            # Atomic write: temp file + rename
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode='w', dir=self.cache_dir, delete=False, suffix='.tmp'
            ) as f:
                f.write(json.dumps(self._cache, indent=2))
                tmp_name = f.name
            os.replace(tmp_name, self.cache_file)
            os.chmod(self.cache_file, 0o600)
        except Exception as e:
            print(f"[zie-framework] CacheManager._save: {e}", file=os.stderr)

    def _session_key(self, session_id: str) -> str:
        """Return session-scoped key prefix."""
        return f"session:{session_id}"

    def _is_expired(self, entry: dict) -> bool:
        """Check if cache entry is expired based on TTL."""
        if "expires_at" not in entry:
            return False
        return time.time() > entry["expires_at"]

    def get(self, key: str, session_id: str) -> Optional[Any]:
        """Get cached value (TTL-aware).

        Args:
            key: Cache key (e.g., "roadmap", "adrs", "project_md")
            session_id: Session identifier for isolation

        Returns:
            Cached value if present and not expired, else None
        """
        session_key = self._session_key(session_id)
        full_key = f"{session_key}:{key}"

        entry = self._cache.get(full_key)
        if entry is None:
            return None

        if self._is_expired(entry):
            # Lazy deletion on read
            del self._cache[full_key]
            self._save()
            return None

        return entry.get("value")

    def set(self, key: str, value: Any, session_id: str, ttl: int) -> None:
        """Set cached value with TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            session_id: Session identifier
            ttl: Time-to-live in seconds
        """
        session_key = self._session_key(session_id)
        full_key = f"{session_key}:{key}"

        self._cache[full_key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time(),
        }
        self._save()

    def delete(self, key: str, session_id: str) -> None:
        """Delete specific key from cache."""
        session_key = self._session_key(session_id)
        full_key = f"{session_key}:{key}"

        if full_key in self._cache:
            del self._cache[full_key]
            self._save()

    def clear_session(self, session_id: str) -> None:
        """Clear all cache entries for a session."""
        session_key = self._session_key(session_id)
        prefix = f"{session_key}:"

        keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]

        if keys_to_delete:
            self._save()

    def get_or_compute(
        self,
        key: str,
        session_id: str,
        compute_fn: Callable[[], Any],
        ttl: int,
    ) -> Any:
        """Cache-or-compute helper.

        Args:
            key: Cache key
            session_id: Session identifier
            compute_fn: Function to call on cache miss (no arguments)
            ttl: Time-to-live in seconds

        Returns:
            Cached value or computed value
        """
        cached = self.get(key, session_id)
        if cached is not None:
            return cached

        # Compute and cache
        value = compute_fn()
        self.set(key, value, session_id, ttl)
        return value


# ── Global cache instance (lazy initialization) ───────────────────────────────

_cache_manager: Optional[CacheManager] = None


def get_cache_manager(cwd: Path) -> CacheManager:
    """Get or create global cache manager instance.

    Args:
        cwd: Project root directory

    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        cache_dir = cwd / ".zie" / "cache"
        _cache_manager = CacheManager(cache_dir)
    return _cache_manager


# ── Convenience helpers for common cache operations ───────────────────────────

def read_roadmap_unified(
    roadmap_path: Path,
    session_id: str,
    cwd: Path,
    ttl: int = 600,
) -> str:
    """Read ROADMAP.md content using unified cache.

    Args:
        roadmap_path: Path to ROADMAP.md
        session_id: Session identifier
        cwd: Project root
        ttl: Cache TTL in seconds (default: 600)

    Returns:
        ROADMAP content string, or empty string on error
    """
    cache = get_cache_manager(cwd)

    def _read() -> str:
        try:
            return roadmap_path.read_text()
        except Exception:
            return ""

    return cache.get_or_compute("roadmap", session_id, _read, ttl)


def read_adrs_unified(
    decisions_dir: Path,
    session_id: str,
    cwd: Path,
    ttl: int = 3600,
) -> str:
    """Read all ADRs and return combined content.

    Args:
        decisions_dir: Path to zie-framework/decisions/
        session_id: Session identifier
        cwd: Project root
        ttl: Cache TTL in seconds (default: 3600)

    Returns:
        Combined ADR content string, or empty string on error
    """
    cache = get_cache_manager(cwd)

    def _read() -> str:
        try:
            adr_files = sorted(decisions_dir.glob("*.md"))
            contents = []
            for adr in adr_files:
                contents.append(adr.read_text())
            return "\n\n".join(contents)
        except Exception:
            return ""

    return cache.get_or_compute("adrs", session_id, _read, ttl)


def read_project_context_unified(
    context_path: Path,
    session_id: str,
    cwd: Path,
    ttl: int = 300,
) -> str:
    """Read project context.md using unified cache.

    Args:
        context_path: Path to project/context.md
        session_id: Session identifier
        cwd: Project root
        ttl: Cache TTL in seconds (default: 300)

    Returns:
        Context content string, or empty string on error
    """
    cache = get_cache_manager(cwd)

    def _read() -> str:
        try:
            return context_path.read_text()
        except Exception:
            return ""

    return cache.get_or_compute("project_md", session_id, _read, ttl)


def get_content_hash_cached(
    cwd: Path,
    session_id: str,
    ttl: int = 1800,
) -> str:
    """Get content hash from unified cache, or compute if miss.

    Uses session-id salt to prevent cross-session pollution.
    Default TTL: 1800s (30 minutes)

    Args:
        cwd: Project root
        session_id: Session identifier
        ttl: Cache TTL in seconds (default: 1800)

    Returns:
        SHA-256 hex digest string, or empty string if files don't exist
    """
    def compute_fn() -> str:
        hasher = hashlib.sha256()
        found = False
        for path in (
            cwd / "zie-framework" / "decisions" / "ADR-000-summary.md",
            cwd / "zie-framework" / "project" / "context.md",
        ):
            try:
                if path.exists():
                    hasher.update(path.read_bytes())
                    found = True
            except Exception:
                continue
        return hasher.hexdigest() if found else ""

    cache = get_cache_manager(cwd)
    return cache.get_or_compute("content_hash", session_id, compute_fn, ttl)
