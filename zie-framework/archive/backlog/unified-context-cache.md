---
tags: [feature]
---

# Unified Context Cache — Session-Scoped ROADMAP/ADR Parsing

## Problem

Each hook reads ROADMAP.md independently with 30s-600s TTLs; ADR directory scanned by load-context on every invocation. 6+ disk reads per session for same data; duplicate parsing logic; content-hash computed 3× per session.

## Motivation

Centralize all caching logic into single session-scoped cache. Reduce disk reads, eliminate duplicate parsing, make TTL policy explicit.

## Rough Scope

**In:**
- `hooks/utils_cache.py` (new) — CacheManager class with TTL policies
- `.zie/cache/session-cache.json` — ROADMAP/ADR parsed (session-scoped)
- Update 6 consumers: intent-sdlc.py, subagent-context.py, session-resume.py, load-context skill, reviewers
- Single API: `cache.get("roadmap", session_id)` / `cache.set(...)`

**Out:**
- Cross-session cache invalidation (handled by content-hash cache)
- External cache services (Redis, etc.)

<!-- priority: HIGH -->
<!-- depends_on: none -->
