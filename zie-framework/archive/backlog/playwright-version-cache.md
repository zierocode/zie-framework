---
tags: [performance]
---

# Cache Playwright Version Check

## Problem

The init hook checks for playwright installation version using a subprocess call every time. This adds ~200ms to every session start. Caching the version for the session would eliminate this overhead.

## Rough Scope

**In:**
- Cache playwright version in `.zie/cache/` with session-scoped TTL
- Check cache before subprocess call — skip subprocess if cache hit and TTL valid
- Invalidate on new session (session-scoped, not global 24h)
- Fallback to direct check on cache miss

**Out:**
- Removing the CVE check (security-critical, must keep)
- Changing the cache location (must use `.zie/cache/` convention)

## Priority

LOW