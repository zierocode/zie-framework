---
approved: true
backlog: backlog/content-hash-ttl-increase.md
---

# Content-Hash TTL Increase — 600s → 1800s

## Summary

Increase content-hash cache TTL from 10 minutes to 30 minutes and add session-ID salt to prevent cross-session cache pollution.

## Problem Statement

Current state:
- Content-hash cache uses 600s (10 min) TTL
- Hash recomputes every 10 minutes for long sessions
- Hash computation reads 2 files (VERSION, plugin.json)
- No session isolation — potential cross-session cache pollution
- Unnecessary for stable sessions where version files don't change

## Goals

1. **Reduce recomputation**: TTL 600s → 1800s (10min → 30min)
2. **Session isolation**: Add session-ID salt to cache key
3. **Maintain correctness**: Hash still updates when files change
4. **Update tests**: Reflect new TTL value

## Non-Goals

- Other cache TTL changes (handled by unified-context-cache)
- Content-hash algorithm changes
- File change detection improvements

## Technical Design

### Current Implementation

```python
# hooks/subagent-context.py (lines 30-35)
CONTENT_HASH_TTL = 600  # 10 minutes
CACHE_FILE = Path(".zie/cache/content-hash.json")

def get_content_hash():
    if cache_valid(CACHE_FILE, CONTENT_HASH_TTL):
        return load_cache(CACHE_FILE)
    return compute_and_cache()
```

### Changes Required

```python
# hooks/subagent-context.py
CONTENT_HASH_TTL = 1800  # 30 minutes (CHANGED from 600)
CONTENT_HASH_SALT = os.environ.get("CLAUDE_CODE_SESSION_ID", "default")
CACHE_FILE = Path(".zie/cache/content-hash.json")

def get_content_hash(session_id: str = None):
    # Salt cache key with session ID
    salted_key = f"content-hash:{session_id or CONTENT_HASH_SALT}"
    
    if cache_valid(CACHE_FILE, CONTENT_HASH_TTL, key=salted_key):
        return load_cache(CACHE_FILE, key=salted_key)
    
    hash_value = compute_hash([
        "VERSION",
        "plugin.json",
        "CLAUDE.md",
        "PROJECT.md"
    ])
    
    save_cache(CACHE_FILE, salted_key, hash_value)
    return hash_value

def compute_hash(files: list[str]) -> str:
    """Compute SHA256 hash of file contents + mtime."""
    hasher = hashlib.sha256()
    for filepath in files:
        p = Path(filepath)
        if p.exists():
            hasher.update(p.read_text().encode())
            hasher.update(str(p.stat().st_mtime).encode())
    return hasher.hexdigest()[:16]
```

### Cache File Format

```json
{
  "content-hash:session-abc123": {
    "value": "a1b2c3d4e5f6g7h8",
    "timestamp": 1712937600,
    "expires_at": 1712939400
  },
  "content-hash:session-xyz789": {
    "value": "x1y2z3a4b5c6d7e8",
    "timestamp": 1712937600,
    "expires_at": 1712939400
  }
}
```

## Testing Plan

1. **Unit tests** (`tests/test_content_hash.py`):
   - Test new TTL (1800s) honored
   - Test session isolation (different session IDs → different cache entries)
   - Test hash recomputation after TTL expiry
   - Test hash recomputation when files change

2. **Integration test**:
   - Run long session (>10min)
   - Verify hash not recomputed before 30min
   - Verify hash updates after file change

## Migration Plan

1. Update `CONTENT_HASH_TTL` constant: 600 → 1800
2. Add session-ID salt to cache key
3. Update `get_content_hash()` to accept session_id param
4. Update tests for new TTL and session isolation
5. Deploy and monitor cache hit rate

## Rollback Plan

If issues arise:
1. Revert TTL to 600s
2. Remove session-ID salt
3. Original cache behavior restored

## Success Criteria

- [ ] TTL increased to 1800s
- [ ] Session-ID salt prevents cross-session pollution
- [ ] Hash computation reduced by ~66% (3× less frequent)
- [ ] Tests updated and passing
- [ ] No stale cache issues in long sessions
