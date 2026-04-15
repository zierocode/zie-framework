---
tags: [feature]
---

# Consolidate Caching Systems

## Problem

Three independent caching mechanisms coexist, unaware of each other:
1. `CacheManager` (`.zie/cache/session-cache.json`) — TTL-based, used by 3 hooks
2. Legacy mtime cache (`/tmp/zie-{sid}/roadmap-cache.json`) — mtime-based, used by 2 hooks
3. Ad-hoc `/tmp` flags (20+ files via `project_tmp_path()`) — no TTL, no invalidation

A ROADMAP read cached in system 1 does not prevent a read in system 2 or 3. Additionally, compact-tier flags use a naming pattern that `session-cleanup.py` never cleans up (different prefix).

## Motivation

Three caching systems for the same data category means 2-3 redundant reads per session, 20+ orphaned temp files, and developer confusion about which cache to use. Consolidating into CacheManager eliminates redundancy and provides a single, testable caching interface.

## Rough Scope

**In:**
- Migrate legacy mtime-based `read_roadmap_cached()` into CacheManager (with mtime invalidation option)
- Migrate frequently-used `/tmp` flags into CacheManager key-value store (dedup, session flags, compact tier)
- Keep ad-hoc `/tmp` flags for one-off coordination (session-resume cache flag) — not all need CacheManager
- Fix compact-tier flag naming to match session-cleanup pattern
- Add CacheManager TTL option for "session-scoped" (expire at session end)

**Out:**
- Removing all `/tmp` usage (some are legitimate for inter-process coordination)
- Changing CacheManager's JSON format