---
tags: [chore]
---

# Consolidate ROADMAP Caching

## Problem

Two independent caching systems exist for ROADMAP.md content:
1. `CacheManager` in `utils_cache.py` — TTL-based, used by session-resume, intent-sdlc, subagent-context
2. `read_roadmap_cached()` in `utils_roadmap.py` — mtime-based, used by sdlc-compact, failure-context

They never share entries. Additionally, 4 hooks read ROADMAP directly from disk bypassing both caches: wip-checkpoint, stop-handler, session-stop, session-learn.

On a typical session, ROADMAP is physically read 5+ times despite caching. On Stop events, 3 separate hooks read it independently.

## Motivation

Consolidating to a single CacheManager eliminates redundant disk I/O and removes confusion about which cache to use. The TTL-based CacheManager is already the standard — migrating all hooks to use it is straightforward.

## Rough Scope

**In:**
- Migrate `read_roadmap_cached()` callers (sdlc-compact, failure-context) to use CacheManager
- Migrate direct-read hooks (wip-checkpoint, stop-handler, session-stop, session-learn) to use CacheManager
- Remove `read_roadmap_cached()` from utils_roadmap.py (dead code after migration)
- Increase ROADMAP TTL from 600s to 1800s (file rarely changes mid-session)
- Pass `roadmap_content` to `is_track_active()` instead of re-reading

**Out:**
- Changing CacheManager architecture (separate item: cache-systems-consolidate)
- Changing ROADMAP format