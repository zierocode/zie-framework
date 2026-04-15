---
date: 2026-04-15
status: approved
slug: cache-systems-consolidate
---

## Problem

Three independent caching mechanisms coexist, unaware of each other:

1. **CacheManager** (`.zie/cache/session-cache.json`) — TTL-based, used by 3 hooks for ROADMAP/ADR/context/hash
2. **Legacy mtime cache** (`/tmp/zie-{sid}/roadmap-cache.json` + `/tmp/zie-kh-{hash}.mtime`) — mtime-gated, used by `utils_roadmap.py` and `knowledge-hash.py`
3. **Ad-hoc `/tmp` flags** (20+ files via `project_tmp_path()`) — no TTL, no invalidation, orphaned between sessions

A ROADMAP read cached in system 1 does not prevent a read in system 2. Compact-tier flags use `zie-{project}-compact-tier-*` naming that `session-cleanup.py` only catches via the `zie-{project}-*` glob — but the legacy roadmap cache uses `zie-{sid}/` directory structure that requires a separate cleanup loop. Result: 2-3 redundant reads per session, orphaned temp files, and developer confusion.

## Solution

Extend `CacheManager` to support two new invalidation modes alongside existing TTL:

- **mtime** — validate against file modification time (replaces `utils_roadmap.py` mtime cache)
- **session-scoped** — expire at session end via `clear_session()` (replaces `/tmp` flags for dedup, compact-tier, design-mode, session-context)

Migrate `read_roadmap_cached()` and `knowledge-hash.py` mtime logic into `CacheManager.get_or_compute()` with `invalidation="mtime"`. Migrate frequently-used `/tmp` flags into `CacheManager` key-value with `invalidation="session"`. Keep `/tmp` for one-off inter-process coordination (session-resume cache flag).

Fix `project_tmp_path()` naming so all flags match the `zie-{project}-` prefix that `session-cleanup.py` already globs — eliminating the separate `zie-*/` directory cleanup loop.

## Rough Scope

**In:** CacheManager mtime mode, session-scoped mode, migrate `read_roadmap_cached`, migrate `knowledge-hash` mtime gate, migrate 6-8 frequent `/tmp` flags, fix compact-tier naming, remove `utils_roadmap.py` legacy cache functions, simplify `session-cleanup.py`.

**Out:** Removing all `/tmp` usage, changing CacheManager's JSON format, migrating one-off coordination flags (session-resume).

## Files Changed

- `hooks/utils_cache.py` — add mtime + session-scoped invalidation modes
- `hooks/utils_roadmap.py` — remove legacy cache functions, delegate to CacheManager
- `hooks/knowledge-hash.py` — use CacheManager mtime mode instead of `/tmp` mtime file
- `hooks/session-cleanup.py` — remove legacy roadmap-cache cleanup, rely on CacheManager `clear_session()`
- `hooks/sdlc-compact.py` — use CacheManager session-scoped flags instead of `/tmp`
- `hooks/stop-handler.py` — same, fix compact-tier flag naming
- `hooks/intent-sdlc.py` — migrate dedup/flags to CacheManager
- `hooks/subagent-context.py` — migrate session-context flag
- `hooks/design-tracker.py` — migrate design-mode flag
- `tests/test_cache_manager.py` — new invalidation mode tests