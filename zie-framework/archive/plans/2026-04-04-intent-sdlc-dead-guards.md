# Implementation Plan: intent-sdlc Dead Guards Cleanup

**Slug:** `intent-sdlc-dead-guards`
**Spec:** `zie-framework/specs/2026-04-04-intent-sdlc-dead-guards-design.md`
**Date:** 2026-04-04

## Steps

### 1. Edit `hooks/intent-sdlc.py`

**Remove dead constant (line 22):**
```python
# DELETE this line:
MAX_MESSAGE_LEN = 1000
```

**Remove dead guard (lines 250–251):**
```python
# DELETE these two lines:
if len(message) > MAX_MESSAGE_LEN:
    sys.exit(0)
```

**Fix redundant strip (line 269):**
```python
# BEFORE:
if len(message.strip()) < 15:
# AFTER:
if len(message) < 15:
```

### 2. Verify existing test still covers the length boundary

`tests/unit/test_hooks_intent_sdlc.py::TestEarlyExitGuards::test_long_message_no_output`
uses a 1100-char prompt. After removing the 1000-char guard the 500-char guard still fires — test remains valid, no change needed.

### 3. Run tests

```bash
make test-fast
```

All tests must pass (zero new failures, zero regressions).

## Estimated Effort

~10 min (3 line deletions + 1 line edit + test run).
