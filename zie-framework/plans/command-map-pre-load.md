---
approved: true
spec: specs/2026-04-14-command-map-pre-load-design.md
---

# Implementation Plan: Command Map Pre-Load

## Overview

Cache command list extraction from SKILL.md in plugin-state cache. Invalidate on SKILL.md mtime change. Save ~345 tokens per session.

## Tasks

### Phase 1: Cache Implementation

1. **Add `CommandMapCache` class to `hooks/session-resume.py`**
   ```python
   class CommandMapCache:
       def __init__(self, session_id: str)
       def get() -> dict[str, str]
       def _parse_skill() -> dict[str, str]
       def _set_cache(command_map: dict)
       def invalidate()
   ```
   - Cache file: `.zie/cache/plugin-state.json`
   - TTL: 86400s (24 hours)
   - Store: `value`, `skill_mtime`, `skill_path`, `cached_at`

2. **Implement `_parse_skill()` method**
   - Parse SKILL.md with regex pattern:
     ```python
     pattern = r'\|\s*`(/[^`]+)`\s*\|\s*([^|]+)\|'
     ```
   - Extract all 19 commands with descriptions

3. **Implement mtime-based invalidation**
   - Check SKILL.md mtime on cache read
   - Invalidate cache if mtime changed
   - Re-parse and re-cache

### Phase 2: Integration

4. **Update `on_session_start()` handler**
   - Initialize `CommandMapCache` with session ID
   - Use cached command map for context injection
   - Fast path: return cached commands in <1ms

### Phase 3: Testing

5. **Create `tests/test_command_map_cache.py`**
   - Test cache hit (mtime unchanged)
   - Test cache miss (mtime changed)
   - Test parsing accuracy (all 19 commands)
   - Test TTL expiration

6. **Integration tests**
   - Session start → verify command map loaded
   - Modify SKILL.md → verify cache invalidated
   - Measure token usage before/after

7. **Token audit**
   - Measure token savings (target: ~345 tokens/session)
   - Verify session start time <100ms

## Acceptance Criteria

- [ ] All 19 commands detected
- [ ] Cache hit on unchanged SKILL.md
- [ ] Cache invalidation on SKILL.md change
- [ ] Token usage reduced by ~345 tokens/session
- [ ] Session start time <100ms
- [ ] All tests passing

## Estimated Effort

- Phase 1: ~1.5 hours
- Phase 2: ~30 min
- Phase 3: ~1 hour
- **Total: ~3 hours**
