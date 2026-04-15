---
approved: true
spec: specs/2026-04-14-test-lookup-caching-design.md
---

# Implementation Plan: Test Lookup Caching

## Overview

Cache test→source file mappings to eliminate duplicate `rglob` lookups on every file edit. Implement per-file debounce instead of global debounce.

## Tasks

### Phase 1: Cache Structure

1. **Create test lookup cache in `hooks/auto-test.py`**
   - Add `TestLookupCache` class:
     ```python
     class TestLookupCache:
         def __init__(self, session_id: str)
         def get_test_for_source(source_path: str) -> Optional[str]
         def set_test_mapping(source_path: str, test_path: str)
         def find_matching_test(source_path: str) -> Optional[str]
         def invalidate_on_test_change(test_path: str)
         def should_debounce(source_path: str) -> bool
     ```
   - Cache structure in `.zie/cache/test-cache.json`:
     - `mappings`: source → test file paths
     - `debounce`: per-file debounce state
     - `test_file_hashes`: test file content hashes for invalidation

### Phase 2: Integration with auto-test.py

2. **Update `find_matching_test()` function**
   - Check cache first before `rglob` lookup
   - Cache result after `rglob` lookup
   - Return cached test path if file still exists

3. **Update debounce logic**
   - Change from global debounce to per-file debounce
   - Debounce delay: 5 seconds per file
   - Store `last_edit` timestamp per source file

4. **Add cache invalidation**
   - Invalidate mapping when test file changes
   - Full invalidation when source file changes

### Phase 3: PostToolUse Handler Update

5. **Update `on_post_tool_use()` handler**
   - Initialize `TestLookupCache` with session ID
   - Use per-file debounce check
   - Use cached test lookup

### Phase 4: Testing

6. **Create `tests/test_test_lookup_cache.py`**
   - Test cache hit/miss
   - Test per-file debounce behavior
   - Test cache invalidation on test change
   - Test `rglob` fallback when cache miss

7. **Integration tests**
   - Edit source file twice within 5s → verify one test run
   - Edit source file twice >5s apart → verify two test runs
   - Modify test file → verify cache invalidated

8. **Performance test**
   - Measure `rglob` calls before/after (target: N→1 per source file)

## Acceptance Criteria

- [ ] `TestLookupCache` class implemented
- [ ] Duplicate `rglob` eliminated
- [ ] Per-file debounce working (5s delay)
- [ ] Cache invalidation on test file change
- [ ] Test runs not missed
- [ ] False positive debounces reduced
- [ ] All tests passing

## Estimated Effort

- Phase 1: ~1.5 hours
- Phase 2: ~1.5 hours
- Phase 3: ~30 min
- Phase 4: ~1.5 hours
- **Total: ~5 hours**
