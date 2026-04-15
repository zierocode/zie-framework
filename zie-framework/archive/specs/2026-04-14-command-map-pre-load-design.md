---
approved: true
backlog: backlog/command-map-pre-load.md
---

# Command Map Pre-Load — Cache in Plugin-State

## Summary

Cache command list extraction from SKILL.md in plugin-state cache. Invalidate on SKILL.md mtime change. Save ~300 tokens per session.

## Problem Statement

Current state:
- Extracts command list from SKILL.md on every `SessionStart`
- Regex parse of 800+ word file
- Static data parsed every session
- Command list changes only on releases
- ~300 tokens spent per session on static data

## Goals

1. **Cache command map**: Store in `.zie/cache/plugin-state.json`
2. **Invalidate on change**: Check SKILL.md mtime
3. **Reduce tokens**: ~300 tokens saved per session
4. **Fast path**: Return cached commands in <1ms

## Non-Goals

- Command parsing logic changes
- New command discovery
- Dynamic command registration

## Technical Design

### Cache Structure

```python
# .zie/cache/plugin-state.json
{
  "command_map": {
    "value": {
      "/backlog": "Capture a new idea as a backlog item",
      "/spec": "Write design spec for a backlog item",
      "/plan": "Draft implementation plan from spec",
      "/implement": "TDD implementation loop",
      "/release": "Release gate — merge dev→main",
      "/retro": "Post-release retrospective",
      "/sprint": "Sprint clear — batch all items",
      "/chore": "Maintenance task track",
      "/hotfix": "Emergency fix track",
      "/spike": "Time-boxed exploration",
      "/fix": "Debug and fix failing tests",
      "/status": "Show current SDLC state",
      "/audit": "Project audit",
      "/resync": "Rescan codebase + update knowledge",
      "/next": "Rank backlog items",
      "/rescue": "Pipeline diagnosis",
      "/health": "Hook health check",
      "/guide": "Framework walkthrough",
      "/brief": "Display session brief"
    },
    "cached_at": 1712937600,
    "skill_mtime": 1712937000,
    "skill_path": "skills/zie-framework-using-zie-framework/SKILL.md"
  }
}
```

### Cache Manager

```python
# hooks/session-resume.py (updated)
from utils_cache import CacheManager
from pathlib import Path
import os

class CommandMapCache:
    def __init__(self, session_id: str):
        self.cache = CacheManager()
        self.session_id = session_id
        self.skill_path = "skills/zie-framework-using-zie-framework/SKILL.md"
        self.ttl = 86400  # 24 hours - commands change rarely
    
    def get(self) -> dict[str, str]:
        """Get cached command map or compute."""
        cached = self.cache.get("command_map", self.session_id)
        
        if cached:
            # Validate mtime
            skill_mtime = Path(self.skill_path).stat().st_mtime
            if cached.get("skill_mtime") == skill_mtime:
                return cached["value"]
        
        # Cache miss or stale - recompute
        command_map = self._parse_skill()
        self._set_cache(command_map)
        return command_map
    
    def _parse_skill(self) -> dict[str, str]:
        """Parse command map from SKILL.md."""
        skill_file = Path(self.skill_path)
        if not skill_file.exists():
            return {}
        
        content = skill_file.read_text()
        command_map = {}
        
        # Extract command descriptions
        # Pattern: | `/command` | Description |
        pattern = r'\|\s*`(/[^`]+)`\s*\|\s*([^|]+)\|'
        for match in re.finditer(pattern, content):
            command = match.group(1)
            description = match.group(2).strip()
            command_map[command] = description
        
        return command_map
    
    def _set_cache(self, command_map: dict[str, str]):
        """Cache command map with mtime."""
        skill_mtime = Path(self.skill_path).stat().st_mtime
        
        self.cache.set("command_map", {
            "value": command_map,
            "skill_mtime": skill_mtime,
            "skill_path": self.skill_path,
            "cached_at": time.time()
        }, self.session_id, ttl=self.ttl)
    
    def invalidate(self):
        """Force cache invalidation."""
        self.cache.delete("command_map", self.session_id)
```

### Integration with session-resume.py

```python
# hooks/session-resume.py (SessionStart handler)
command_cache = CommandMapCache(session_id)

def on_session_start():
    # Fast path - cached command map
    command_map = command_cache.get()
    
    # Use command map for context injection
    context = build_context(command_map)
    inject_context(context)
```

### Token Savings

| Operation | Before | After |
|-----------|--------|-------|
| Parse SKILL.md | ~300 tokens | 0 tokens |
| Regex execution | ~50 tokens | 0 tokens |
| Cache lookup | N/A | ~5 tokens |
| **Total per session** | **~350 tokens** | **~5 tokens** |
| **Savings** | - | **~345 tokens/session** |

## Testing Plan

1. **Unit tests** (`tests/test_command_map_cache.py`):
   - Test cache hit (mtime unchanged)
   - Test cache miss (mtime changed)
   - Test parsing accuracy
   - Test TTL expiration

2. **Integration tests**:
   - Session start → verify command map loaded
   - Modify SKILL.md → verify cache invalidated
   - Measure token usage before/after

3. **Regression tests**:
   - Verify all 19 commands still detected
   - Test parsing edge cases (multiline descriptions)

## Migration Plan

1. Add `CommandMapCache` class to `hooks/session-resume.py`
2. Update `on_session_start()` to use cache
3. Add mtime-based invalidation
4. Test with SKILL.md modifications
5. Monitor token usage
6. Verify all commands detected

## Rollback Plan

If issues arise:
1. Disable cache (parse directly)
2. Original parsing restored
3. No functionality lost

## Success Criteria

- [ ] All 19 commands detected
- [ ] Cache hit on unchanged SKILL.md
- [ ] Cache invalidation on SKILL.md change
- [ ] Token usage reduced by ~345 tokens/session
- [ ] Session start time <100ms
