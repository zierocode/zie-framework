---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-counter-valueerror.md
---

# Guard wip-checkpoint Counter File Against ValueError on Corrupt Content — Design Spec

**Problem:** `wip-checkpoint.py` line 39 calls `int(counter_file.read_text().strip())` inside a `try/except Exception` block, but the current source shows this is already partially guarded — the real risk is that a corrupt file (non-numeric content) causes `ValueError`, which IS caught by the broad `except Exception` clause; however the counter resets to `0` rather than to `0` with proper recovery, meaning `count` stays at `0` after the exception, then increments to `1` — which is actually the correct recovery behaviour. The spec is to verify this is working correctly and add an explicit test that documents the contract.

**Approach:** Add a test to `test_hooks_wip_checkpoint.py` that pre-writes a corrupt (non-numeric) counter file, runs the hook, and asserts: (1) the hook exits with `returncode == 0`; (2) the counter file is subsequently written with a valid integer; (3) stderr may contain the warning message. If the current implementation does NOT gracefully recover (i.e. `count` remains wrong), patch `wip-checkpoint.py` line 38-41 to use an explicit `except (ValueError, OSError)` with `count = 0` reset and remove the bare `except Exception` to be more precise.

**Components:**
- `hooks/wip-checkpoint.py` — lines 37-41 (counter read block)
- `tests/unit/test_hooks_wip_checkpoint.py` — new test in `TestWipCheckpointCounter`

**Data Flow — test cases to add:**

1. `test_corrupt_counter_file_resets_gracefully`:
   - Write `"not-a-number\n"` to the counter file path for `tmp_path.name`.
   - Run hook with `ZIE_MEMORY_API_KEY="fake-key"` and `ZIE_MEMORY_API_URL="https://localhost:19999"`.
   - Assert `r.returncode == 0`.
   - Assert counter file now contains `"1"` (reset to 0, incremented to 1).
   - Assert `r.stderr` contains `"wip-checkpoint"` (the warning was printed).

2. `test_whitespace_only_counter_file_resets_gracefully`:
   - Write `"   \n"` to counter file (whitespace only — `int("") → ValueError`).
   - Same assertions as above.

3. `test_empty_counter_file_resets_gracefully`:
   - Write `""` to counter file.
   - Assert `returncode == 0` and counter file contains `"1"`.

**Edge Cases:**
- Current code: `count = 0` is initialised before the `try` block; if `int(...)` raises, `count` stays `0` and the `except` prints to stderr. Then `count += 1` → `1`. This is correct recovery behaviour — the test verifies this contract is maintained if the implementation is ever refactored.
- If the counter file is deleted between `counter_file.exists()` check and `counter_file.read_text()` (TOCTOU), an `OSError` is raised — this is also caught by `except Exception`. The test for this case is an OS-level race and is out of scope for unit tests.
- Counter file with `"5 "` (trailing space) is already handled by `.strip()` — no new test needed.

**Out of Scope:**
- Changing the checkpoint frequency (`CHECKPOINT_EVERY = 5`).
- Adding file locking to the counter (not needed for single-process hooks).
- Testing TOCTOU races (integration concern).
