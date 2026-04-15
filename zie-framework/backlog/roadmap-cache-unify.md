---
tags: [chore]
---

# Consolidate Caching: Unify ROADMAP Cache + Adopt CacheManager Everywhere

## Problem

Three overlapping caching issues found in lean audit:

1. **Dual ROADMAP cache**: `CacheManager` (TTL-based) and `read_roadmap_cached()` (mtime-based) never share entries. 4 hooks (wip-checkpoint, stop-handler, session-stop, session-learn) bypass both caches entirely and read from disk directly. On a typical session, ROADMAP is physically read 5+ times.

2. **Subagent-context uncached reads**: `subagent-context.py` reads `project/context.md` directly from disk for ADR counting, despite `read_project_context_unified()` and `read_adrs_unified()` being available in `utils_cache.py`. It also globs+stats plan files without caching.

3. **ROADMAP Now parsed 5+ times per session**: session-resume, intent-sdlc, subagent-context, failure-context, and sdlc-compact all independently parse the same "Now" section. The "Active: {feature}" string appears 2-5 times, wasting 200-500 tokens.

## Motivation

Consolidating to a single CacheManager eliminates redundant disk I/O, removes confusion about which cache to use, and reduces token waste from duplicate context injection. The TTL-based CacheManager is already the standard — migrating all hooks to use it is straightforward.

## Rough Scope

**In:**
- Migrate `read_roadmap_cached()` callers (sdlc-compact, failure-context) to use CacheManager
- Migrate direct-read hooks (wip-checkpoint, stop-handler, session-stop, session-learn) to use CacheManager
- Remove `read_roadmap_cached()` from utils_roadmap.py (dead code after migration)
- Increase ROADMAP TTL from 600s to 1800s (file rarely changes mid-session)
- Pass `roadmap_content` to `is_track_active()` instead of re-reading
- Replace direct `context_file.read_text()` in subagent-context with `read_project_context_unified()`
- Replace ADR regex counting in subagent-context with `read_adrs_unified()` from CacheManager
- Cache plan file glob results (short TTL)
- Create session-scoped "Now item" singleton: first hook writes to cache, subsequent hooks read from cache instead of parsing ROADMAP again
- Invalidate Now-item cache on Write/Edit to ROADMAP.md

**Out:**
- Changing CacheManager JSON format
- Changing hook output format
- Removing Now item context from any hook (each hook still outputs its own formatted line)