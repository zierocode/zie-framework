# Design Spec: wip-checkpoint Modulo Guard

**Slug:** `wip-checkpoint-modulo-guard`
**Date:** 2026-04-04
**Status:** Approved

## Problem

`wip-checkpoint.py` writes the edit counter to disk on every Edit/Write event via
`safe_write_persistent` (NamedTemporaryFile + os.replace + os.chmod = 3 syscalls),
then immediately exits if `count % 5 != 0`. Four out of five writes are wasted I/O.

## Goal

Move the `safe_write_persistent` call inside the `if count % CHECKPOINT_EVERY == 0`
block so the counter file is only written when a checkpoint actually fires.

## Behaviour Change

| Scenario | Before | After |
| --- | --- | --- |
| Edit 1–4 (non-checkpoint) | read → increment → **write** → skip | read → increment → skip (no write) |
| Edit 5, 10, … (checkpoint) | read → increment → write → proceed | read → increment → proceed → **write** |
| Corrupt counter file | resets → writes 1 → skips (1%5≠0) | resets → skips → no write |

## Acceptance Criteria

1. `safe_write_persistent` is called only when `count % CHECKPOINT_EVERY == 0`.
2. Non-checkpoint edits (count 1–4) produce **no write** to the counter file.
3. Checkpoint edit (count == 5) writes the counter and triggers the memory API call.
4. Corrupt/empty counter defaults to `count = 1` and exits without writing (1%5 ≠ 0).
5. All existing guardrails (no API key, no zf dir, bad URL, outer guard) are unchanged.
6. `test_counter_increments_each_call` is updated: counter file absent after 3 calls
   (since none hit modulo-5); or seeded at 2 and called 3× so edit 5 fires and writes.
7. `test_missing_roadmap_no_crash`, `test_empty_now_section_no_crash`,
   `test_malformed_now_items_graceful_skip`, `test_corrupt_counter_file_resets_gracefully`,
   `test_whitespace_only_counter_file_resets_gracefully`, `test_empty_counter_file_resets_gracefully`
   — all drop the `counter.exists()` + value assertions (counter not written on edit 1).
8. `test_no_crash_on_fifth_edit_with_bad_url` remains: counter is pre-seeded to 4,
   fifth call triggers write; assert still passes.
9. All other tests pass unchanged.
10. `make test-fast` green.

## Non-Goals

- No change to checkpoint frequency (every 5 edits).
- No change to `safe_write_persistent` internals.
- No change to memory API call logic.
