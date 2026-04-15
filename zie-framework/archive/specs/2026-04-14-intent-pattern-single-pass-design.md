---
approved: true
backlog: backlog/intent-pattern-single-pass.md
---

# Intent Pattern Single-Pass Regex — 65 Checks → 1

## Summary

Refactor intent detection from 65 sequential regex checks to a single combined regex with named groups. Cache last 10 messages for deduplication.

## Problem Statement

Current state:
- 13 intent categories × ~5 patterns = ~65 regex checks per message
- Patterns checked sequentially
- No early-exit on first match
- Short-message gate exits early but still scans all patterns
- No message deduplication

## Goals

1. **Single regex**: Combine all patterns into one regex with named groups
2. **One-pass match**: Extract intent + params in single regex execution
3. **Message cache**: Cache last 10 messages for deduplication
4. **Maintain coverage**: All 13 intent categories still detected

## Non-Goals

- New intent categories
- Intent classification algorithm changes (ML, etc.)
- Context window management

## Technical Design

### Current Implementation

```python
# hooks/intent-sdlc.py (lines 85-140)
INTENT_PATTERNS = {
    "backlog": [r"add (?:a )?backlog item", r"capture (?:this )?idea", ...],
    "spec": [r"write (?:a )?spec", r"design document", ...],
    "plan": [r"plan (?:this|the)", r"implementation plan", ...],
    "implement": [r"implement", r"code (?:this|it)", ...],
    "release": [r"release", r"merge to main", ...],
    "retro": [r"retrospective", r"retro", ...],
    "sprint": [r"sprint", r"batch process", ...],
    "chore": [r"chore", r"maintenance", ...],
    "hotfix": [r"hotfix", r"emergency fix", ...],
    "spike": [r"spike", r"explore", ...],
    "fix": [r"fix (?:this|the)", r"debug", ...],
    "status": [r"status", r"current state", ...],
    "audit": [r"audit", r"security review", ...],
}

def detect_intent(message: str) -> Optional[str]:
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return intent
    return None
```

### New Implementation

```python
# hooks/intent-sdlc.py
import re
from collections import OrderedDict

# Single combined regex with named groups
INTENT_REGEX = re.compile(r"""
    (?P<backlog>
        add\s+(?:a\s+)?backlog\s+item |
        capture\s+(?:this\s+)?idea |
        new\s+(?:feature|item) |
        backlog\s+(?:item|idea)
    )
    |
    (?P<spec>
        write\s+(?:a\s+)?spec |
        design\s+document |
        specification |
        design\s+phase
    )
    |
    (?P<plan>
        plan\s+(?:this|the) |
        implementation\s+plan |
        how\s+to\s+implement |
        implementation\s+strategy
    )
    |
    (?P<implement>
        implement |
        code\s+(?:this|it) |
        build\s+(?:this|it) |
        write\s+(?:the\s+)?code
    )
    |
    (?P<release>
        release |
        merge\s+to\s+main |
        ship\s+(?:it)? |
        version\s+bump
    )
    |
    (?P<retro>
        retrospective |
        retro |
        lessons?\s+learned
    )
    |
    (?P<sprint>
        sprint |
        batch\s+process |
        clear\s+backlog
    )
    |
    (?P<chore>
        chore |
        maintenance |
        cleanup |
        refactor
    )
    |
    (?P<hotfix>
        hotfix |
        emergency\s+fix |
        critical\s+fix
    )
    |
    (?P<spike>
        spike |
        explore |
        research\s+task |
        time-boxed
    )
    |
    (?P<fix>
        fix\s+(?:this|the) |
        debug |
        bug\s+fix |
        something's?\s+broken
    )
    |
    (?P<status>
        status |
        current\s+state |
        where\s+are\s+we |
        progress
    )
    |
    (?P<audit>
        audit |
        security\s+review |
        compliance\s+check
    )
""", re.IGNORECASE | re.VERBOSE)

# Message cache for deduplication
from collections import deque
_message_cache = deque(maxlen=10)

def detect_intent(message: str) -> Optional[tuple[str, dict]]:
    """
    Detect intent with single regex pass.
    Returns (intent, params) tuple or None.
    """
    # Check for duplicate message
    if message in _message_cache:
        return None  # Duplicate - skip
    
    _message_cache.append(message)
    
    # Single regex match
    match = INTENT_REGEX.search(message)
    if not match:
        return None
    
    # Extract intent from named group
    for intent_name, matched_text in match.groupdict().items():
        if matched_text:
            return (intent_name, {
                "matched_text": matched_text,
                "confidence": "high" if matched_text.lower() in message.lower() else "medium"
            })
    
    return None

def get_intent_categories() -> list[str]:
    """Return list of all intent categories."""
    return list(INTENT_REGEX.groupindex.keys())
```

### Message Cache

```python
# hooks/utils_message_cache.py (new)
from collections import deque
import hashlib

class MessageCache:
    def __init__(self, maxlen: int = 10):
        self._cache = deque(maxlen=maxlen)
        self._hashes = set()
    
    def is_duplicate(self, message: str) -> bool:
        """Check if message is duplicate."""
        msg_hash = hashlib.sha256(message.encode()).hexdigest()[:16]
        if msg_hash in self._hashes:
            return True
        
        # Evict oldest if at capacity
        if len(self._cache) >= self._cache.maxlen:
            old = self._cache[0]
            old_hash = hashlib.sha256(old.encode()).hexdigest()[:16]
            self._hashes.discard(old_hash)
        
        self._cache.append(message)
        self._hashes.add(msg_hash)
        return False
    
    def clear(self):
        """Clear message cache."""
        self._cache.clear()
        self._hashes.clear()

# Global instance
message_cache = MessageCache()
```

### Performance Comparison

| Metric | Before | After |
|--------|--------|-------|
| Regex compilations | 65 | 1 |
| Regex executions (avg) | 32.5 | 1 |
| Message dedup | No | Yes (last 10) |
| Memory | Minimal | ~1KB for cache |

## Testing Plan

1. **Unit tests** (`tests/test_intent_detection.py`):
   - Test all 13 intent categories detected
   - Test duplicate message detection
   - Test regex performance (single pass)
   - Test edge cases (ambiguous messages)

2. **Integration tests**:
   - Send 100 messages → verify deduplication
   - Measure intent detection latency (expect: 10× faster)

3. **Regression tests**:
   - Verify all existing intent patterns still match
   - Test false positive rate unchanged

## Migration Plan

1. Create combined regex pattern
2. Add message cache utility
3. Update `detect_intent()` to use single regex
4. Update tests for new return format (tuple vs string)
5. Deploy and monitor intent detection accuracy
6. Measure performance improvement

## Rollback Plan

If issues arise:
1. Revert to sequential pattern matching
2. Disable message cache
3. Original behavior restored

## Success Criteria

- [ ] All 13 intent categories detected
- [ ] Duplicate messages skipped
- [ ] Regex execution time <1ms (was ~10ms)
- [ ] No false positives introduced
- [ ] Tests passing
