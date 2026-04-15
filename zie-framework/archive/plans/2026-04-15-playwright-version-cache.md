---
date: 2026-04-15
status: approved
slug: playwright-version-cache
---

# Implementation Plan: Playwright Version Cache

## Steps

1. **Add `get_playwright_version_cached()` to `hooks/utils_cache.py`**
   - New function: `get_playwright_version_cached(session_id: str, cwd: Path, ttl: int = 600) -> str`
   - Uses `CacheManager.get_or_compute("playwright_version", session_id, compute_fn, ttl)`
   - `compute_fn` runs `subprocess.run(["playwright", "--version"], capture_output=True, text=True, timeout=5)` and returns the raw stdout (e.g. `"1.55.1"`)
   - On subprocess failure (FileNotFoundError, OSError, timeout), return empty string — no cache entry created, so next call retries

2. **Refactor `_check_playwright_version()` in `hooks/session-resume.py`**
   - Replace direct `subprocess.run(["playwright", "--version"], ...)` with `get_playwright_version_cached(session_id, cwd)`
   - Keep all existing error handling, CVE comparison, and `config["playwright_enabled"] = False` logic unchanged
   - Add `session_id` and `cwd` parameters to `_check_playwright_version(config, session_id, cwd)`

3. **Update caller in `session-resume.py`**
   - Pass `session_id` and `cwd` to `_check_playwright_version()` (both already available in the hook)

## Tests

- **test_playwright_version_cache_miss**: Mock subprocess, verify it's called once and result cached
- **test_playwright_version_cache_hit**: Pre-populate cache, verify subprocess is not called
- **test_playwright_version_cache_failure**: Mock subprocess to raise `FileNotFoundError`, verify empty string returned, no cache entry created
- **test_playwright_version_below_minimum**: Cached version below `PLAYWRIGHT_MIN_VERSION` disables `playwright_enabled`
- **test_playwright_version_at_minimum**: Cached version at minimum keeps `playwright_enabled` unchanged

## Acceptance Criteria

- `_check_playwright_version()` uses cached version on second call within same session
- Subprocess call skipped when cache hit with valid TTL
- CVE comparison logic unchanged — versions below minimum still disable playwright
- Subprocess failure does not create a cache entry (retries on next call)
- All existing tests still pass (`make test-fast`)