---
approved: true
backlog: backlog/unified-context-cache.md
---

# Unified Context Cache — Session-Scoped ROADMAP/ADR Parsing

## Summary

Centralize all context caching (ROADMAP, ADRs, project knowledge) into a single session-scoped cache manager. Eliminate duplicate disk reads and parsing across 6+ hooks per session.

## Problem Statement

Current state:
- Each hook reads ROADMAP.md independently with inconsistent TTLs (30s-600s)
- ADR directory scanned by `load-context` skill on every invocation
- 6+ disk reads per session for identical data
- Duplicate parsing logic across `intent-sdlc.py`, `subagent-context.py`, `session-resume.py`
- Content-hash computed 3× per session for same files

## Goals

1. **Single source of truth**: One cache manager for all context data
2. **Session scoping**: Cache lives in `.zie/cache/session-cache.json`, keyed by session ID
3. **TTL policy**: Explicit, configurable TTLs per data type
4. **Reduce I/O**: From 6+ reads to 1 read per session for ROADMAP/ADRs
5. **API simplicity**: `cache.get("roadmap", session_id)` / `cache.set("roadmap", data, ttl)`

## Non-Goals

- Cross-session cache invalidation (handled by content-hash cache)
- External cache services (Redis, Memcached)
- Distributed caching

## Technical Design

### Cache Manager Class

```python
# hooks/utils_cache.py (new)
from pathlib import Path
import json
import time
from typing import Any, Optional

class CacheManager:
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path(".zie/cache")
        self.cache_file = self.cache_dir / "session-cache.json"
        self._ensure_cache_dir()
        self._cache = self._load()
    
    def _ensure_cache_dir(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _load(self) -> dict:
        if self.cache_file.exists():
            with open(self.cache_file) as f:
                return json.load(f)
        return {"sessions": {}}
    
    def _save(self):
        with open(self.cache_file, "w") as f:
            json.dump(self._cache, f, indent=2)
    
    def get(self, key: str, session_id: str) -> Optional[Any]:
        """Get cached value for session. Returns None if expired or missing."""
        session = self._cache.get("sessions", {}).get(session_id, {})
        if key not in session:
            return None
        
        entry = session[key]
        if time.time() > entry.get("expires_at", 0):
            self.delete(key, session_id)
            return None
        
        return entry.get("value")
    
    def set(self, key: str, value: Any, session_id: str, ttl: int = 300):
        """Set cached value with TTL (seconds). Default TTL: 5min."""
        if "sessions" not in self._cache:
            self._cache["sessions"] = {}
        if session_id not in self._cache["sessions"]:
            self._cache["sessions"][session_id] = {}
        
        self._cache["sessions"][session_id][key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time()
        }
        self._save()
    
    def delete(self, key: str, session_id: str):
        """Delete specific key from session cache."""
        if session_id in self._cache.get("sessions", {}):
            self._cache["sessions"][session_id].pop(key, None)
            self._save()
    
    def clear_session(self, session_id: str):
        """Clear all cache for a session."""
        self._cache.get("sessions", {}).pop(session_id, None)
        self._save()
    
    def get_or_compute(self, key: str, session_id: str, compute_fn: callable, ttl: int = 300) -> Any:
        """Get from cache or compute and cache result."""
        value = self.get(key, session_id)
        if value is not None:
            return value
        
        value = compute_fn()
        self.set(key, value, session_id, ttl)
        return value
```

### TTL Configuration

```python
# hooks/config.py (add)
CACHE_TTLS = {
    "roadmap": 600,      # 10 min - changes per sprint
    "adrs": 3600,        # 1 hour - rarely changes
    "project_md": 300,   # 5 min - may change during session
    "command_map": 1800, # 30 min - changes per release
    "test_map": 300,     # 5 min - changes with test edits
}
```

### Consumers Update

Update these 6 consumers to use `CacheManager`:

1. **hooks/intent-sdlc.py**
   ```python
   from utils_cache import CacheManager
   cache = CacheManager()
   roadmap = cache.get_or_compute("roadmap", session_id, parse_roadmap, CACHE_TTLS["roadmap"])
   ```

2. **hooks/subagent-context.py**
   ```python
   adrs = cache.get_or_compute("adrs", session_id, scan_adrs, CACHE_TTLS["adrs"])
   ```

3. **hooks/session-resume.py**
   ```python
   project_md = cache.get_or_compute("project_md", session_id, read_project, CACHE_TTLS["project_md"])
   ```

4. **skills/zie-framework-load-context/SKILL.md**
   ```python
   adrs = cache.get_or_compute("adrs", session_id, scan_adrs, CACHE_TTLS["adrs"])
   ```

5. **hooks/auto-test.py** (for test mapping, separate cache)
6. **skills/zie-framework-impl-reviewer/SKILL.md**

### File Structure

```text
hooks/
  utils_cache.py        # NEW: CacheManager class
  config.py             # ADD: CACHE_TTLS dict
  intent-sdlc.py        # UPDATE: use cache
  subagent-context.py   # UPDATE: use cache
  session-resume.py     # UPDATE: use cache
  auto-test.py          # UPDATE: use cache (test mapping)
.zie/
  cache/
    session-cache.json  # NEW: session-scoped cache
    test-cache.json     # Separate: test→source mapping
```

## Testing Plan

1. **Unit tests** (`tests/test_cache_manager.py`):
   - Test TTL expiration
   - Test session isolation
   - Test get_or_compute caching
   - Test concurrent access safety

2. **Integration tests**:
   - Verify ROADMAP parsed once per session
   - Verify ADR scan once per session
   - Verify cache invalidation on file change

3. **Performance test**:
   - Measure disk reads before/after (expect: 6→1 per session)

## Migration Plan

1. Create `hooks/utils_cache.py` with `CacheManager` class
2. Add `CACHE_TTLS` to `hooks/config.py`
3. Update consumers one at a time, testing each:
   - `session-resume.py` first (lowest risk)
   - `intent-sdlc.py` second
   - `subagent-context.py` third
   - `load-context` skill fourth
   - `auto-test.py` fifth (uses separate test-cache)
   - Reviewers last
4. Run full test suite after each consumer update
5. Remove duplicate parsing code after all consumers migrated

## Rollback Plan

If issues arise:
1. Revert consumer changes one at a time
2. Keep `utils_cache.py` for future use
3. Original parsing logic remains as fallback

## Success Criteria

- [ ] Disk reads reduced from 6+ to 1 per session
- [ ] No duplicate parsing across hooks
- [ ] All 6 consumers using `CacheManager`
- [ ] Tests pass (unit + integration)
- [ ] Session isolation verified (no cross-session pollution)
