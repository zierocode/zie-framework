# intent-sdlc: Remove Redundant Length Guards + Dead MAX_MESSAGE_LEN Constant

## Problem

`intent-sdlc.py:248-269` has two issues: (1) `MAX_MESSAGE_LEN` is set to 1000 but a separate guard at line 252 exits on `len(message) > 500` — `MAX_MESSAGE_LEN` is never reached and is a dead constant. (2) The inner guard at line 269 calls `message.strip()` on a string already stripped at line 246 — a no-op allocation on every prompt.

## Motivation

Dead constants mislead future maintainers about the actual length gate. The redundant `.strip()` call is negligible but is a code smell on the hottest path in the hook system (fires on every prompt). Clean removal improves clarity and removes micro-overhead.

## Rough Scope

- Remove or consolidate the duplicate length checks
- Remove `MAX_MESSAGE_LEN` constant (or align it to the actual 500-char gate)
- Remove the redundant `.strip()` in the inner guard
- Update tests for length boundary behavior
