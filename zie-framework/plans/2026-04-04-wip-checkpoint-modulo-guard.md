# Plan: wip-checkpoint Modulo Guard

**Slug:** `wip-checkpoint-modulo-guard`
**Spec:** `zie-framework/specs/2026-04-04-wip-checkpoint-modulo-guard-design.md`
**Date:** 2026-04-04

## Steps

### 1 — Fix `hooks/wip-checkpoint.py`

Move `safe_write_persistent` inside the checkpoint block.

Current (lines 46–52):
```python
count += 1
safe_write_persistent(counter_file, str(count))

# Only checkpoint every 5 edits
CHECKPOINT_EVERY = 5
if count % CHECKPOINT_EVERY != 0:
    sys.exit(0)
```

New:
```python
count += 1

# Only checkpoint every 5 edits
CHECKPOINT_EVERY = 5
if count % CHECKPOINT_EVERY != 0:
    sys.exit(0)

safe_write_persistent(counter_file, str(count))
```

### 2 — Update `tests/unit/test_hooks_wip_checkpoint.py`

**`TestWipCheckpointCounter.test_counter_increments_each_call`**
- Counter file will not exist after 3 calls (none hit modulo-5).
- Options: assert counter absent, OR seed to 2 then call 3× so edit 5 writes.
- Use simpler approach: assert counter absent (3 non-checkpoint edits → no write).

**`TestWipCheckpointRoadmapEdgeCases`** — three tests:
- `test_missing_roadmap_no_crash`
- `test_empty_now_section_no_crash`
- `test_malformed_now_items_graceful_skip`
- All assert `counter.exists()` and `counter.read_text().strip() == "1"`.
- Remove both assertions (hook exits at modulo gate before writing on edit 1).

**`TestWipCheckpointCounter`** — three corrupt/empty counter tests:
- `test_corrupt_counter_file_resets_gracefully` — asserts counter == "1" after run.
- `test_whitespace_only_counter_file_resets_gracefully` — same.
- `test_empty_counter_file_resets_gracefully` — same.
- After fix: count resets to 1, 1%5≠0 → no write. Counter file retains original corrupt content.
- Update assertions: counter file still exists (pre-written by test setup) but value
  unchanged OR remove value assertions and just assert returncode == 0.
- Keep `assert "wip-checkpoint" in r.stderr` for the corrupt/whitespace tests (parse error
  still logged).

**`test_no_crash_on_fifth_edit_with_bad_url`** (line 121) — unchanged: counter
pre-seeded to 4, fifth call hits 5%5==0 → write happens → assert counter == "5" still passes.

### 3 — Verify

```bash
make test-fast
```

All tests green. No regressions.

## Files Touched

| File | Change |
| --- | --- |
| `hooks/wip-checkpoint.py` | Move `safe_write_persistent` inside checkpoint block |
| `tests/unit/test_hooks_wip_checkpoint.py` | Update 6 tests to drop counter-write assertions |
