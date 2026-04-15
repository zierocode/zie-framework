---
tags: [chore]
---

# Session-Scoped Config Cache

## Problem

`load_config()` in `utils_config.py` reads and parses `zie-framework/.config` from disk on every call with no caching. It is called by 6+ hooks independently (safety-check, auto-test, stop-handler, failure-context, sdlc-compact, session-resume). On a typical session with 50 tool calls, that's 50+ redundant reads of the same static file.

## Motivation

Config rarely changes during a session. A session-scoped cache (similar to CacheManager for ROADMAP) would eliminate 50+ redundant disk reads per session, reducing I/O overhead on the hot path (safety-check fires on every Write/Edit/Bash).

## Rough Scope

**In:**
- Add TTL-based in-memory cache to `load_config()` using CacheManager pattern
- Cache key: `config:{project_name}`, TTL: session duration (or 3600s)
- Invalidate on ConfigChange event (already handled by config-drift.py)
- Update all callers to benefit from cache (no API change needed — cache is transparent)

**Out:**
- Changing the CacheManager itself (separate item)
- Changing config file format