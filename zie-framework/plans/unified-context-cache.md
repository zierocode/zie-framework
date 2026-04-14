---
approved: true
spec: specs/2026-04-14-unified-context-cache-design.md
---

# Implementation Plan: Unified Context Cache

## Overview

Create a session-scoped cache manager to centralize ROADMAP, ADRs, and project knowledge caching. Eliminate duplicate disk reads across 6+ hooks per session.

## Tasks

### Phase 1: Core Infrastructure

1. **Create `hooks/utils_cache.py`**
   - Implement `CacheManager` class with methods:
     - `__init__(cache_dir: Path)` — initialize cache directory
     - `_load() -> dict` — load cache from `.zie/cache/session-cache.json`
     - `_save()` — persist cache to disk
     - `get(key, session_id) -> Optional[Any]` — get cached value (TTL-aware)
     - `set(key, value, session_id, ttl)` — set cached value with TTL
     - `delete(key, session_id)` — delete specific key
     - `clear_session(session_id)` — clear all session cache
     - `get_or_compute(key, session_id, compute_fn, ttl)` — cache-or-compute helper
   - Add TTL expiration logic using `time.time()`

2. **Add `CACHE_TTLS` to `hooks/config.py`**
   ```python
   CACHE_TTLS = {
       "roadmap": 600,      # 10 min
       "adrs": 3600,        # 1 hour
       "project_md": 300,   # 5 min
       "command_map": 1800, # 30 min
       "test_map": 300,     # 5 min
   }
   ```

### Phase 2: Consumer Updates (in order)

3. **Update `hooks/session-resume.py`** (lowest risk)
   - Import `CacheManager` from `utils_cache`
   - Replace project MD parsing with `cache.get_or_compute("project_md", ...)`
   - Test: session start loads project context once

4. **Update `hooks/intent-sdlc.py`**
   - Import `CacheManager` from `utils_cache`
   - Replace ROADMAP parsing with `cache.get_or_compute("roadmap", ...)`
   - Test: intent detection uses cached ROADMAP

5. **Update `hooks/subagent-context.py`**
   - Import `CacheManager` from `utils_cache`
   - Replace ADR scan with `cache.get_or_compute("adrs", ...)`
   - Test: subagent context uses cached ADRs

6. **Update `skills/zie-framework-load-context/SKILL.md`**
   - Import `CacheManager` from `utils_cache`
   - Replace ADR scan with `cache.get_or_compute("adrs", ...)`
   - Test: load-context skill uses cached ADRs

7. **Update `hooks/auto-test.py`**
   - Import `CacheManager` from `utils_cache`
   - Use cache for test mapping (separate from session cache)
   - Test: auto-test uses cached test→source mappings

8. **Update `skills/zie-framework-impl-reviewer/SKILL.md`**
   - Import `CacheManager` from `utils_cache`
   - Use cache for context loading
   - Test: reviewer uses cached context

### Phase 3: Testing

9. **Create `tests/test_cache_manager.py`**
   - Test TTL expiration
   - Test session isolation (no cross-session pollution)
   - Test `get_or_compute` caching behavior
   - Test concurrent access safety

10. **Integration tests**
    - Verify ROADMAP parsed once per session
    - Verify ADR scan once per session
    - Verify cache invalidation on file change

11. **Performance test**
    - Measure disk reads before/after (target: 6→1 per session)

### Phase 4: Cleanup

12. **Remove duplicate parsing code**
    - After all consumers migrated, remove old parsing logic
    - Verify no regressions

## Acceptance Criteria

- [ ] `CacheManager` class implemented with all methods
- [ ] `CACHE_TTLS` configured in `config.py`
- [ ] All 6 consumers using `CacheManager`
- [ ] Session isolation verified (no cross-session pollution)
- [ ] Disk reads reduced from 6+ to 1 per session
- [ ] All tests passing (unit + integration)
- [ ] No duplicate parsing logic remaining

## Estimated Effort

- Phase 1: ~2 hours
- Phase 2: ~4 hours (6 consumers × 40 min each)
- Phase 3: ~1.5 hours
- Phase 4: ~30 min
- **Total: ~8 hours**
