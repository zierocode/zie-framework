---
tags: [performance]
---

# Intent-SDLC Hook — Lean Pattern Matching

## Problem

The `intent-sdlc` hook (`hooks/intent_sdlc.py`) has grown to 65+ regex patterns and does redundant work — checking all patterns on every prompt even when most won't match.

## Rough Scope

**In:**
- Combine regex patterns into single combined regex (alternation group)
- Add early-exit for short messages (< 50 chars) — skip pattern matching entirely
- Cache compiled pattern on first use (module-level or lru_cache)
- Reduce from 65+ individual `re.search()` calls to 1 combined pattern match

**Out:**
- Removing patterns or changing intent detection behavior
- Changing the hook's output format

## Priority

MEDIUM