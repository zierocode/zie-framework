# Design Spec: intent-sdlc Dead Guards Cleanup

**Slug:** `intent-sdlc-dead-guards`
**Date:** 2026-04-04
**Status:** Approved

## Problem

`hooks/intent-sdlc.py` has two dead-code issues in its outer guard block (lines 248–269):

1. `MAX_MESSAGE_LEN = 1000` (line 22) is never reached — a `len(message) > 500` guard at line 252 exits first.
2. `message.strip()` at line 269 is a no-op — `message` was already `.strip()`-ped at line 246.

## Proposed Fix

1. Remove `MAX_MESSAGE_LEN` constant and the `len(message) > MAX_MESSAGE_LEN` guard (lines 22 and 250–251). The actual gate is 500 chars; no constant needed.
2. Replace `len(message.strip()) < 15` with `len(message) < 15` at line 269.

## Acceptance Criteria

- `MAX_MESSAGE_LEN` constant is gone from the file.
- The `len(message) > MAX_MESSAGE_LEN` guard is gone.
- Inner guard reads `len(message) < 15` (no `.strip()`).
- Existing test `test_long_message_no_output` (1100-char prompt → no output) still passes.
- `make test-fast` green.

## Out of Scope

- Changing the 500-char or 15-char threshold values.
- Any other hook files.
