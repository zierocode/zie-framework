---
approved: true
backlog: backlog/test-lookup-caching.md
---

# Test Lookup Caching — Test→Source Mapping

## Summary

Cache test→source file mappings to eliminate duplicate `rglob` lookups on every file edit. Debounce per-file instead of globally.

## Problem Statement

Current state:
- `find_matching_test()` in `auto-test.py` called twice per file edit
- Debounce check scans file list on every `PostToolUse:Edit`
- Duplicate `rglob` for same test file
- Debounce state not shared across edits
- No cache invalidation when test files change

## Goals

1. **Cache test→source mappings**: One lookup per source file
2. **Per-file debounce**: Debounce keyed by source file, not global
3. **Cache invalidation**: Invalidate when test file changes
4. **Reduce I/O**: Eliminate duplicate `rglob` scans

## Non-Goals

- Test running logic changes
- Test discovery algorithm changes
- Coverage tracking changes

## Technical Design

### Cache Structure

```python
# .zie/cache/test-cache.json
{
  "mappings": {
    "hooks/intent-sdlc.py": "tests/test_intent_sdlc.py",
    "hooks/subagent-context.py": "tests/test_subagent_context.py",
    "skills/zie-framework-spec/SKILL.md": "tests/test_spec_skill.py"
  },
  "debounce": {
    "hooks/intent-sdlc.py": {
      "last_edit": 1712937600,
      "scheduled_run": null
    }
  },
  "test_file_hashes": {
    "tests/test_intent_sdlc.py": "abc123",
    "tests/test_subagent_context.py": "def456"
  }
}
```

### Cache Manager Integration

```python
# hooks/auto-test.py
from utils_cache import CacheManager

class TestLookupCache:
    def __init__(self, session_id: str):
        self.cache = CacheManager()
        self.session_id = session_id
        self.debounce_delay = 5  # seconds
    
    def get_test_for_source(self, source_path: str) -> Optional[str]:
        """Get cached test file for source path."""
        mappings = self.cache.get("test_mappings", self.session_id) or {}
        return mappings.get(source_path)
    
    def set_test_mapping(self, source_path: str, test_path: str):
        """Cache test→source mapping."""
        mappings = self.cache.get("test_mappings", self.session_id) or {}
        mappings[source_path] = test_path
        self.cache.set("test_mappings", mappings, self.session_id, ttl=1800)
    
    def find_matching_test(self, source_path: str) -> Optional[str]:
        """Find test file with caching."""
        # Check cache first
        cached = self.get_test_for_source(source_path)
        if cached and Path(cached).exists():
            return cached
        
        # rglob lookup
        source_name = Path(source_path).stem
        test_patterns = [
            f"tests/test_{source_name}.py",
            f"tests/*/{source_name}_test.py",
            f"tests/*/*{source_name}*.py"
        ]
        
        for pattern in test_patterns:
            for test_file in Path(".").rglob(pattern):
                if test_file.exists():
                    self.set_test_mapping(source_path, str(test_file))
                    return str(test_file)
        
        return None
    
    def invalidate_on_test_change(self, test_path: str):
        """Invalidate mappings when test file changes."""
        mappings = self.cache.get("test_mappings", self.session_id) or {}
        to_remove = [k for k, v in mappings.items() if v == test_path]
        for key in to_remove:
            del mappings[key]
        self.cache.set("test_mappings", mappings, self.session_id, ttl=1800)
    
    def should_debounce(self, source_path: str) -> bool:
        """Check if edit should be debounced (per-file)."""
        debounce_state = self.cache.get("debounce", self.session_id) or {}
        file_state = debounce_state.get(source_path, {})
        
        last_edit = file_state.get("last_edit", 0)
        now = time.time()
        
        if now - last_edit < self.debounce_delay:
            return True  # Still in debounce window
        
        # Update debounce state
        file_state["last_edit"] = now
        debounce_state[source_path] = file_state
        self.cache.set("debounce", debounce_state, self.session_id, ttl=300)
        return False
```

### Integration with auto-test.py

```python
# hooks/auto-test.py (PostToolUse handler)
test_cache = TestLookupCache(session_id)

def on_post_tool_use(tool_name, tool_input):
    if tool_name != "Edit":
        return
    
    source_path = tool_input.get("file_path")
    
    # Per-file debounce
    if test_cache.should_debounce(source_path):
        return  # Skip - still in debounce window
    
    # Find test with caching
    test_path = test_cache.find_matching_test(source_path)
    if test_path:
        schedule_test_run(test_path)
```

### Cache Invalidation Strategy

```python
# hooks/session-start.py or file watcher
def on_file_modified(filepath):
    if filepath.startswith("tests/"):
        test_cache.invalidate_on_test_change(filepath)
    elif filepath.startswith("hooks/") or filepath.startswith("skills/"):
        # Source changed - may need to find new test
        test_cache.delete("test_mappings", session_id)  # Full invalidation
```

## Testing Plan

1. **Unit tests** (`tests/test_test_lookup_cache.py`):
   - Test cache hit/miss
   - Test per-file debounce
   - Test cache invalidation
   - Test rglob fallback

2. **Integration tests**:
   - Edit source file twice within 5s → one test run
   - Edit source file twice >5s apart → two test runs
   - Modify test file → cache invalidated

3. **Performance test**:
   - Measure rglob calls before/after (expect: N→1 per source file)

## Migration Plan

1. Add `TestLookupCache` class to `hooks/auto-test.py`
2. Update `find_matching_test()` to use cache
3. Update debounce logic to per-file
4. Add cache invalidation on test file change
5. Test with rapid edits
6. Monitor test run frequency

## Rollback Plan

If issues arise:
1. Disable cache (use rglob directly)
2. Revert to global debounce
3. Original behavior restored

## Success Criteria

- [ ] Duplicate rglob eliminated
- [ ] Per-file debounce working
- [ ] Cache invalidation on test change
- [ ] Test runs not missed
- [ ] False positive debounces reduced
