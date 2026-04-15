---
date: 2026-04-15
status: approved
slug: playwright-version-cache
---

# Cache Playwright Version Check

## Problem

`_check_playwright_version()` in `session-resume.py` runs `subprocess.run(["playwright", "--version"])` on every session start, adding ~200ms even when the result hasn't changed since the last check within the same session.

## Solution

Use the existing `CacheManager.get_or_compute()` to cache the playwright version string per session. On cache hit (same session, TTL valid), skip the subprocess call entirely. The CVE safety check still runs — we only skip the version *lookup*, not the comparison against `PLAYWRIGHT_MIN_VERSION`.

Add a convenience helper `get_playwright_version_cached()` in `utils_cache.py` that wraps the subprocess call behind `get_or_compute("playwright_version", ...)`. Then refactor `_check_playwright_version()` to call the cached helper instead of running `subprocess.run` directly.

## Rough Scope

**In:**
- New `get_playwright_version_cached()` helper in `utils_cache.py` (TTL=600s, session-scoped)
- Refactor `_check_playwright_version()` to use cached version string
- Unit tests for cache hit/miss paths

**Out:**
- Removing or weakening the CVE comparison (safety-critical, must stay)
- Changing cache location or format (must follow `.zie/cache/session-cache.json` convention)

## Files Changed

- `hooks/utils_cache.py` — add `get_playwright_version_cached()` helper
- `hooks/session-resume.py` — refactor `_check_playwright_version()` to use cached version
- `tests/test_cache_manager.py` — add tests for playwright version cache hit/miss