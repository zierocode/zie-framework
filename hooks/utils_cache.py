#!/usr/bin/env python3
"""Unified session-scoped cache manager for zie-framework hooks.

Centralizes ROADMAP, ADRs, and project knowledge caching. Eliminates duplicate
disk reads across 6+ hooks per session.

Cache location: .zie/cache/session-cache.json
Session isolation: keyed by session_id to prevent cross-session pollution.
Invalidation modes: ttl (time-based), mtime (file-change), session (clear_session).
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

from utils_error import log_error


class CacheManager:
    """Session-scoped cache manager with TTL, mtime, and session invalidation.

    Usage:
        cache = CacheManager(Path(".zie/cache"))
        value = cache.get("roadmap", session_id)
        cache.set("roadmap", content, session_id, ttl=600)

        # Or use cache-or-compute helper:
        value = cache.get_or_compute("roadmap", session_id, compute_fn, ttl=600)

        # mtime invalidation — invalidate when source file changes:
        cache.set("roadmap", content, session_id, ttl=600,
                   invalidation="mtime", source_path=roadmap_path)
        cache.get_or_compute("roadmap", session_id, compute_fn, ttl=600,
                              invalidation="mtime", source_path=roadmap_path)

        # session invalidation — persists until clear_session():
        cache.set("flag", True, session_id, ttl=0, invalidation="session")
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
            print(f"[zf] CacheManager._save: {e}", file=sys.stderr)

    def _session_key(self, session_id: str) -> str:
        """Return session-scoped key prefix."""
        return f"session:{session_id}"

    def _is_expired(self, entry: dict) -> bool:
        """Check if cache entry is expired based on invalidation mode."""
        invalidation = entry.get("invalidation", "ttl")

        if invalidation == "session":
            # Session-scoped entries never expire by time
            return False

        if invalidation == "mtime":
            # Invalidate if source file mtime has changed
            source_path = entry.get("source_path")
            stored_mtime = entry.get("mtime")
            if source_path and stored_mtime is not None:
                try:
                    current_mtime = os.path.getmtime(source_path)
                    if abs(current_mtime - stored_mtime) > 0.001:
                        return True
                except OSError:
                    return True
            # Fall through to TTL check
        # ttl invalidation (default) — check expires_at
        if "expires_at" not in entry:
            return False
        return time.time() > entry["expires_at"]

    def get(self, key: str, session_id: str) -> Optional[Any]:
        """Get cached value (invalidation-aware).

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

    def set(
        self,
        key: str,
        value: Any,
        session_id: str,
        ttl: int = 600,
        invalidation: str = "ttl",
        source_path: Optional[str] = None,
    ) -> None:
        """Set cached value with invalidation mode.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            session_id: Session identifier
            ttl: Time-to-live in seconds (default 600; used only for "ttl" mode)
            invalidation: One of "ttl" (default), "mtime", or "session".
                - "ttl": expire after ttl seconds
                - "mtime": expire when source_path's mtime changes
                - "session": persist until clear_session() (expires_at=inf)
            source_path: Required when invalidation="mtime". File path whose mtime
                is tracked to detect changes.
        """
        session_key = self._session_key(session_id)
        full_key = f"{session_key}:{key}"

        entry: dict = {
            "value": value,
            "created_at": time.time(),
            "invalidation": invalidation,
        }

        if invalidation == "mtime":
            if source_path is None:
                raise ValueError("source_path is required for mtime invalidation")
            entry["source_path"] = str(source_path)
            try:
                entry["mtime"] = os.path.getmtime(source_path)
            except OSError:
                entry["mtime"] = 0.0
            entry["expires_at"] = time.time() + ttl  # fallback TTL for mtime
        elif invalidation == "session":
            entry["expires_at"] = float("inf")
        else:
            # ttl mode (default)
            entry["expires_at"] = time.time() + ttl

        self._cache[full_key] = entry
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
        ttl: int = 600,
        invalidation: str = "ttl",
        source_path: Optional[str] = None,
    ) -> Any:
        """Cache-or-compute helper.

        Args:
            key: Cache key
            session_id: Session identifier
            compute_fn: Function to call on cache miss (no arguments)
            ttl: Time-to-live in seconds (default 600)
            invalidation: One of "ttl", "mtime", or "session"
            source_path: Required when invalidation="mtime"

        Returns:
            Cached value or computed value
        """
        cached = self.get(key, session_id)
        if cached is not None:
            return cached

        # Compute and cache
        value = compute_fn()
        self.set(key, value, session_id, ttl=ttl,
                 invalidation=invalidation, source_path=source_path)
        return value

    def set_flag(self, key: str, session_id: str) -> None:
        """Set a lightweight boolean flag (session-scoped).

        Equivalent to set(key, True, session_id, invalidation="session").
        Used to replace /tmp flag files.

        Args:
            key: Flag name (e.g., "compact-tier-1", "design-mode")
            session_id: Session identifier
        """
        self.set(key, True, session_id, ttl=0, invalidation="session")

    def has_flag(self, key: str, session_id: str) -> bool:
        """Check if a session-scoped boolean flag is set.

        Args:
            key: Flag name
            session_id: Session identifier

        Returns:
            True if the flag exists and is truthy, False otherwise
        """
        value = self.get(key, session_id)
        return bool(value)


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
    """Read ROADMAP.md content using unified cache with mtime invalidation.

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
        except OSError as e:
            log_error("utils_cache", "read_roadmap", e)
            return ""

    return cache.get_or_compute(
        "roadmap", session_id, _read, ttl,
        invalidation="mtime", source_path=str(roadmap_path),
    )


def read_adrs_unified(
    decisions_dir: Path,
    session_id: str,
    cwd: Path,
    ttl: int = 3600,
    keywords: Optional[list] = None,
) -> str:
    """Read ADRs and return combined content, optionally filtered by keywords.

    Args:
        decisions_dir: Path to zie-framework/decisions/
        session_id: Session identifier
        cwd: Project root
        ttl: Cache TTL in seconds (default: 3600)
        keywords: Optional list of keywords for ADR relevance filter.
            When provided: always include ADR-000-summary, then include
            only ADRs whose filename or first-line title matches any keyword
            (case-insensitive). If no keywords match, fall back to all ADRs.
            If None/empty: load all ADRs (current behavior).

    Returns:
        Combined ADR content string, or empty string on error
    """
    cache = get_cache_manager(cwd)

    # If keywords provided, use a keyword-specific cache key
    cache_key = "adrs"
    if keywords:
        kw_hash = hashlib.md5(" ".join(sorted(keywords)).lower().encode()).hexdigest()[:8]
        cache_key = f"adrs:kw:{kw_hash}"

    def _read() -> str:
        try:
            adr_files = sorted(decisions_dir.glob("*.md"))
            if not adr_files:
                return ""

            # No keywords → load all ADRs (safe default)
            if not keywords:
                contents = []
                for adr in adr_files:
                    contents.append(adr.read_text())
                return "\n\n".join(contents)

            # Keywords provided: filter by relevance
            kw_lower = [k.lower() for k in keywords]
            summary_files = []
            matching_files = []

            for adr in adr_files:
                name_lower = adr.stem.lower()
                # Always collect ADR-000-summary
                if name_lower.startswith("adr-000") or "summary" in name_lower:
                    summary_files.append(adr)
                    continue

                # Match keywords against filename
                if any(kw in name_lower for kw in kw_lower):
                    matching_files.append(adr)
                    continue

                # Match keywords against first line (title)
                try:
                    first_line = adr.read_text().split("\n", 1)[0].lower()
                    if any(kw in first_line for kw in kw_lower):
                        matching_files.append(adr)
                except OSError:
                    continue

            # If no matches, fall back to all ADRs
            if not matching_files:
                contents = []
                for adr in adr_files:
                    contents.append(adr.read_text())
                return "\n\n".join(contents)

            # Return summary + matching ADRs
            result_files = summary_files + matching_files
            contents = []
            for adr in result_files:
                contents.append(adr.read_text())
            return "\n\n".join(contents)
        except OSError as e:
            log_error("utils_cache", "read_adrs", e)
            return ""

    return cache.get_or_compute(cache_key, session_id, _read, ttl)


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
        except OSError as e:
            log_error("utils_cache", "read_project_context", e)
            return ""

    return cache.get_or_compute("project_md", session_id, _read, ttl)


def get_playwright_version_cached(
    session_id: str,
    cwd: Path,
    ttl: int = 600,
) -> str:
    """Get Playwright version string, cached per session.

    Caches the result of `playwright --version` for the session TTL.
    On subprocess failure (not installed, timeout), returns empty string
    without creating a cache entry — so the next call retries.

    Args:
        session_id: Session identifier
        cwd: Project root (for cache directory resolution)
        ttl: Cache TTL in seconds (default: 600)

    Returns:
        Version string (e.g. "1.55.1") or empty string on failure
    """
    import subprocess

    def _get_version() -> str:
        try:
            result = subprocess.run(
                ["playwright", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            raw = result.stdout.strip()
            parts = raw.split()
            return parts[-1] if parts else ""
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return ""

    cache = get_cache_manager(cwd)
    version = cache.get_or_compute("playwright_version", session_id, _get_version, ttl)
    # Don't cache empty results — allow retry on next call
    if version == "":
        cache.delete("playwright_version", session_id)
    return version


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
            except OSError as e:
                log_error("utils_cache", "read_content_hash", e)
                continue
        return hasher.hexdigest() if found else ""

    cache = get_cache_manager(cwd)
    return cache.get_or_compute("content_hash", session_id, compute_fn, ttl)
