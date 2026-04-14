---
tags: [feature]
---

# Test Lookup Caching — test→source mapping

## Problem

`find_matching_test` in auto-test.py called twice per file edit; debounce check scans file list on every PostToolUse:Edit. Duplicate rglob for same test file; debounce state not shared across edits.

## Motivation

Cache test→source mapping eliminates duplicate lookups. Debounce per-file not global reduces false positives.

## Rough Scope

**In:**
- `hooks/auto-test.py` — add test cache
- `.zie/cache/test-cache.json` — test→source mapping
- Cache invalidation on test file change

**Out:**
- Test running logic (unchanged)

<!-- priority: MEDIUM -->
<!-- depends_on: none -->
