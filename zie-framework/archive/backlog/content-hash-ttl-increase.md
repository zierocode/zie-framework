---
tags: [chore]
---

# Content-Hash TTL Increase — 600s → 1800s

## Problem

Content-hash cache uses 600s TTL; recomputes hash every 10min for long sessions. Hash computation reads 2 files; unnecessary for stable sessions.

## Motivation

Increase TTL to 30min reduces redundant hash computation. Add session-id salt to prevent cross-session pollution.

## Rough Scope

**In:**
- `hooks/subagent-context.py` lines 30-35 — change TTL constant 600 → 1800
- Add session-id salt to cache key
- Update tests for new TTL

**Out:**
- Other cache TTLs (handled separately)

<!-- priority: LOW -->
<!-- depends_on: none -->
