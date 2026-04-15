---
tags: [chore]
---

# Cache Playwright Version Check

## Problem

`session-resume.py` spawns `playwright --version` via subprocess on every session start (200-500ms) to check for CVE-2025-59288. The version doesn't change between sessions — this check should be cached.

## Motivation

200-500ms of subprocess overhead per session start for a check that rarely changes. A cached result with 24-hour TTL would eliminate this on subsequent sessions.

## Rough Scope

**In:**
- Cache playwright version check result in CacheManager with 86400s (24h) TTL
- Invalidate cache if playwright package is updated (check mtime of playwright executable)
- Fallback to direct check if cache miss

**Out:**
- Removing the CVE check (security-critical, must keep)