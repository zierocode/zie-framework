---
approved: true
spec: specs/2026-04-14-content-hash-ttl-increase-design.md
---

# Implementation Plan: Content-Hash TTL Increase

## Overview

Increase content-hash cache TTL from 600s to 1800s (10min → 30min) and add session-ID salt to prevent cross-session cache pollution.

## Tasks

### Phase 1: Update Content-Hash Implementation

1. **Update `hooks/subagent-context.py`**
   - Change `CONTENT_HASH_TTL` constant: `600 → 1800`
   - Add session-ID salt:
     ```python
     CONTENT_HASH_SALT = os.environ.get("CLAUDE_CODE_SESSION_ID", "default")
     ```
   - Update `get_content_hash()` function:
     - Accept `session_id: str = None` parameter
     - Create salted key: `f"content-hash:{session_id or CONTENT_HASH_SALT}"`
     - Use salted key for cache lookup/save
   - Update `compute_hash()` to hash 4 files:
     - `VERSION`, `plugin.json`, `CLAUDE.md`, `PROJECT.md`

2. **Update cache file format**
   - Support multiple session-keyed entries in `.zie/cache/content-hash.json`
   - Format:
     ```json
     {
       "content-hash:session-abc123": {
         "value": "a1b2c3d4e5f6g7h8",
         "timestamp": 1712937600,
         "expires_at": 1712939400
       }
     }
     ```

### Phase 2: Testing

3. **Create/update `tests/test_content_hash.py`**
   - Test new TTL (1800s) is honored
   - Test session isolation (different session IDs → different cache entries)
   - Test hash recomputation after TTL expiry
   - Test hash recomputation when version files change

4. **Integration test**
   - Run long session (>10 min)
   - Verify hash NOT recomputed before 30 min
   - Verify hash updates after file change

### Phase 3: Validation

5. **Deploy and monitor**
   - Monitor cache hit rate
   - Verify no stale cache issues in long sessions
   - Measure hash computation frequency (expect: 66% reduction)

## Acceptance Criteria

- [ ] TTL increased to 1800s (30 minutes)
- [ ] Session-ID salt prevents cross-session pollution
- [ ] Hash computation reduced by ~66%
- [ ] Tests updated and passing
- [ ] No stale cache issues in long sessions

## Estimated Effort

- Phase 1: ~1 hour
- Phase 2: ~1 hour
- Phase 3: ~30 min
- **Total: ~2.5 hours**
