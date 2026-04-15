---
approved: true
spec: specs/2026-04-14-intent-pattern-single-pass-design.md
---

# Implementation Plan: Intent Pattern Single-Pass Regex

## Overview

Refactor intent detection from 65 sequential regex checks to a single combined regex with named groups. Add message cache for deduplication (last 10 messages).

## Tasks

### Phase 1: Combined Regex

1. **Update `hooks/intent-sdlc.py`**
   - Create single combined regex with named groups for all 13 intent categories:
     - `backlog`, `spec`, `plan`, `implement`, `release`, `retro`, `sprint`, `chore`, `hotfix`, `spike`, `fix`, `status`, `audit`
   - Use `re.VERBOSE` flag for readability
   - Include all existing patterns from each category

2. **Update `detect_intent()` function**
   - Change return type from `Optional[str]` to `Optional[tuple[str, dict]]`
   - Single regex match instead of nested loops
   - Extract intent from named group
   - Return `(intent_name, params)` tuple with matched text and confidence

### Phase 2: Message Cache

3. **Create `hooks/utils_message_cache.py`**
   - Implement `MessageCache` class:
     ```python
     class MessageCache:
         def __init__(self, maxlen: int = 10)
         def is_duplicate(message: str) -> bool
         def clear()
     ```
   - Use `deque(maxlen=10)` for FIFO cache
   - Use SHA256 hashes for efficient duplicate detection
   - Create global `message_cache` instance

4. **Integrate message cache with `detect_intent()`**
   - Check for duplicate before regex match
   - Skip duplicate messages (return `None`)
   - Add non-duplicate messages to cache

### Phase 3: Testing

5. **Create `tests/test_intent_detection.py`**
   - Test all 13 intent categories detected correctly
   - Test duplicate message detection
   - Test regex performance (single pass)
   - Test edge cases (ambiguous messages)

6. **Integration tests**
   - Send 100 messages → verify deduplication works
   - Measure intent detection latency (target: 10× faster)

7. **Regression tests**
   - Verify all existing intent patterns still match
   - Test false positive rate unchanged

### Phase 4: Performance Validation

8. **Benchmark**
   - Measure regex execution time (target: <1ms, was ~10ms)
   - Measure memory usage (~1KB for cache)
   - Verify 65 regex compilations → 1

## Acceptance Criteria

- [ ] All 13 intent categories detected
- [ ] Duplicate messages skipped (last 10 cached)
- [ ] Regex execution time <1ms
- [ ] No false positives introduced
- [ ] All tests passing
- [ ] Performance improvement verified (10× faster)

## Estimated Effort

- Phase 1: ~1.5 hours
- Phase 2: ~1 hour
- Phase 3: ~1.5 hours
- Phase 4: ~30 min
- **Total: ~4.5 hours**
