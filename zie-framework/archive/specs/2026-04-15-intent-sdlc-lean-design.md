---
date: 2026-04-15
status: approved
slug: intent-sdlc-lean
---

# Intent-SDLC Hook — Lean Pattern Matching

## Problem

`hooks/intent-sdlc.py` runs on every user prompt. INTENT_PATTERN is already a single combined regex (14 named groups), but `NEW_INTENT_REGEXES` still iterates 19 individual `re.search()` calls per invocation. The early-exit threshold is 15 chars — messages 15–49 chars run the full regex pipeline unnecessarily.

## Solution

- Merge `NEW_INTENT_REGEXES` into `INTENT_PATTERN` as additional named groups (`new_sprint`, `new_fix`, `new_chore`), keeping the ≥2 threshold by counting group overlaps in one pass.
- Raise the short-message skip threshold from 15 to 50 characters — messages under 50 chars without a strong keyword match exit early.
- Remove `NEW_INTENT_REGEXES` dict entirely; scoring happens by checking how many of the 3 new-intent groups matched.

## Rough Scope

- Refactor `INTENT_PATTERN` to include `new_sprint`, `new_fix`, `new_chore` named groups
- Replace `NEW_INTENT_REGEXES` iteration with single-pass match + threshold count
- Change `len(message) < 15` guard to `len(message) < 50`
- Update tests to cover new combined behavior

## Files Changed

- `hooks/intent-sdlc.py` — main hook logic
- `tests/test_intent_sdlc.py` — test coverage